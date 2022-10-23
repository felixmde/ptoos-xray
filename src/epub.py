import ebooklib
import logging
import re
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from ebooklib import epub
from src.pokemon import Pokemon
from typing import List, Dict
from rich.progress import track
from rich.console import Console

POKEMON_ID_PREFIX = "pokemon-id-"


def create_pokedex_chapter(pokemon: List[Pokemon]) -> epub.EpubHtml:
    POKEDEX_TITLE = "Pokedex"
    POKEDEX_FILE = "content/np_pokedex.xhtml"
    POKEDEX_UID = "np_pokedex"
    chapter = epub.EpubHtml(
        title=POKEDEX_TITLE, file_name=POKEDEX_FILE, uid=POKEDEX_UID
    )
    content = ["<h1>Pokedex</h1>"]

    for p in pokemon:
        content.append(f'<h2 id="{POKEMON_ID_PREFIX}{p.name.lower()}">{p.name}</h2>')
        content.append(
            f'  <p><img alt="[Pokemon {p.name}]" src="../{p.img_filepath}"/><br/></p>'
        )
        for paragraph in p.description.split("\n"):
            content.append(f"  <p>{paragraph}</p>")
        content.append("")

    chapter.content = "\n".join(content)
    return chapter


def patch_chapter(chapter: epub.EpubHtml, pokemon_lookup: Dict[str, Pokemon]):
    r = re.compile("([:,.!?“”‘’… ]+)")
    soup: BeautifulSoup = BeautifulSoup(chapter.content, "html.parser")

    def pokemon_name_to_link(key: str, word: str) -> Tag:
        tag = soup.new_tag("a")
        tag.string = word
        tag.attrs["href"] = f"np_pokedex.xhtml#{POKEMON_ID_PREFIX}{key}"
        tag.attrs["style"] = "color:black;text-decoration:none"
        return tag

    def patch_string(section: NavigableString) -> List:
        """Replace Pokemon with link to Pokemon; requires splitting up the
        NavigableString into a list of NavigableStrings and Tags."""
        result = [[]]
        for word in r.split(str(section)):
            if word.lower() in pokemon_lookup:
                pokemon_lookup[word.lower()].appears_in_book = True
                link = pokemon_name_to_link(word.lower(), word)
                result.append(link)
                result.append([])
            else:
                result[-1].append(word)

        # convert words back into strings
        for i in range(len(result)):
            if isinstance(result[i], list):
                result[i] = NavigableString("".join(result[i]))
        return result

    def patch_paragraph(paragraph: Tag):
        contents = []
        for section in paragraph.contents:
            if isinstance(section, NavigableString):
                contents += patch_string(section)
            else:
                patch_paragraph(section)
                contents.append(section)
        paragraph.contents = contents

    for p_soup in soup.find_all("p"):
        words_have_changed, words = False, []
        patch_paragraph(p_soup)
    chapter.content = str(soup)


def patch(epub_filepath: str, pokemon: List[Pokemon]):
    book = epub.read_epub(epub_filepath)

    pokemon_lookup = {p.name.lower(): p for p in pokemon}
    chapters = [
        b
        for b in book.get_items()
        if isinstance(b, epub.EpubHtml)
        if b.id.startswith("np_")
    ]
    for c in track(chapters, description="Add Pokemon links to chapters"):
        patch_chapter(c, pokemon_lookup)

    # only add Pokemon to Pokedex chapter that appear (in the book)
    pokemon = [p for p in pokemon if p.appears_in_book]

    chapter = create_pokedex_chapter(pokemon)
    book.add_item(chapter)
    link = epub.Link(chapter.file_name, chapter.title, chapter.id)
    book.toc.append(link)
    book.spine.append((chapter.id, "yes"))

    for p in pokemon:
        image_content = open(p.img_filepath, "rb").read()
        img = epub.EpubItem(
            uid=p.name,
            file_name=p.img_filepath,
            media_type="image/png",
            content=image_content,
        )
        book.add_item(img)

    console = Console()
    epub_out = epub_filepath.replace(".", "-with-links.")
    with console.status(f"Writing {epub_out}"):
        epub.write_epub(epub_out, book, {})
    console.print(f"[green]✓[/green] [orange1]{epub_out}[/orange1] written")
