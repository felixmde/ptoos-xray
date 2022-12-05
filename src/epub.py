import ebooklib
import logging
import re
import sys
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from ebooklib import epub
from src.pokemon import Pokemon
from typing import List, Dict, Optional
from rich.progress import track
from rich.console import Console

POKEMON_ID_PREFIX = "pokemon-id-"
POKEDEX_UID = "np_pokedex"


@dataclass
class AnnoyingPokemon:
    name_chunks: List[str]
    length_chunks: int
    name_in_pokedex: str


ANNOYING_POKEMON = [
    AnnoyingPokemon(["Mr", ".", "Mime"], 3, "mr. mime"),
    AnnoyingPokemon(["farfetch", "’", "d"], 3, "farfetch'd"),
    AnnoyingPokemon(["sirfetch", "’", "d"], 3, "sirfetch'd"),
]


def create_pokedex_chapter(pokemon: List[Pokemon]) -> epub.EpubHtml:
    POKEDEX_TITLE = "Pokedex"
    POKEDEX_FILE = "content/np_pokedex.xhtml"
    chapter = epub.EpubHtml(
        title=POKEDEX_TITLE, file_name=POKEDEX_FILE, uid=POKEDEX_UID
    )
    content = ["<h1>Pokedex</h1>"]

    for p in pokemon:
        content.append(f'<h2 id="{POKEMON_ID_PREFIX}{p.link_id}">{p.name}</h2>')
        content.append(
            f'  <p><img alt="[Pokemon {p.name}]" src="../{p.img_filename}"/><br/></p>'
        )
        for paragraph in p.description.split("\n"):
            content.append(f"  <p>{paragraph}</p>")
        content.append("")

    chapter.content = "\n".join(content)
    return chapter


def patch_chapter(chapter: epub.EpubHtml, pokemon_lookup: Dict[str, Pokemon]):
    special_chars_regex = re.compile("([:,.!?“”‘’… ]+)")
    soup: BeautifulSoup = BeautifulSoup(chapter.content, "html.parser")

    # Set to remember which Pokemon have already gotten a link for that
    # chapter.
    pokemon_added_for_chapter = set()

    def pokemon_to_link(p: Pokemon, name_as_in_book: str) -> Tag:
        tag = soup.new_tag("a")
        tag.string = name_as_in_book
        tag.attrs["href"] = f"np_pokedex.xhtml#{POKEMON_ID_PREFIX}{p.link_id}"
        # tag.attrs["style"] = "color:black;text-decoration:none"
        return tag

    def is_annoying_pokemon(index: int, chunks: List[str]) -> Optional[AnnoyingPokemon]:
        for p in ANNOYING_POKEMON:
            if p.name_chunks == list(
                map(lambda s: s.lower(), chunks[index : index + p.length_chunks])
            ):
                return p
        return None

    def patch_string(section: NavigableString) -> List:
        """Replace Pokemon with link to Pokemon; requires splitting up the
        NavigableString into a list of NavigableStrings and Tags."""
        result = [[]]
        index, chunks = 0, special_chars_regex.split(str(section))
        while index < len(chunks):
            word = chunks[index]
            pokemon: Optional[Pokemon] = None
            increment: int = 1

            if word.lower() in pokemon_lookup:
                pokemon = pokemon_lookup[word.lower()]
            elif annoying_pokemon := is_annoying_pokemon(index, chunks):
                pokemon = pokemon_lookup[annoying_pokemon.name_in_pokedex]
                increment = annoying_pokemon.length_chunks

            if pokemon is not None and pokemon.name in pokemon_added_for_chapter:
                pokemon = None

            if pokemon is not None:
                pokemon_added_for_chapter.add(pokemon.name)
                pokemon.appears_in_book = True
                name = "".join(chunks[index : index + increment])
                link = pokemon_to_link(pokemon, name)
                result.append(link)
                result.append([])
                index += increment
            else:
                result[-1].append(word)
                index += 1

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


def get_pokemon_lookup(pokemon: List[Pokemon]) -> Dict[str, Pokemon]:
    pokemon_lookup = {p.name.lower(): p for p in pokemon}
    pokemon_lookup["nidoran"] = pokemon_lookup["nidoran♂"]
    pokemon_lookup["barrierd"] = pokemon_lookup["mr. mime"]
    return pokemon_lookup


def patch(epub_filename: str, pokemon: List[Pokemon]):
    try:
        book = epub.read_epub(epub_filename)
    except Exception:
        logging.exception("Failed to open epub.")
        sys.exit(1)

    pokemon_lookup = get_pokemon_lookup(pokemon)
    chapters = [
        b
        for b in book.get_items()
        if isinstance(b, epub.EpubHtml)
        if b.id.startswith("np_")
    ]

    if [c for c in chapters if c.id == POKEDEX_UID]:
        logging.warning(f"It looks like '{epub_filename}' already has a Pokedex.")
        sys.exit(1)

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
        image_content = open(p.img_filename, "rb").read()
        img = epub.EpubItem(
            uid=p.name,
            file_name=p.img_filename,
            media_type="image/png",
            content=image_content,
        )
        book.add_item(img)

    console = Console()
    epub_out = epub_filename.replace(".", "-with-links.")
    with console.status(f"Writing {epub_out}"):
        epub.write_epub(epub_out, book, {})
    console.print(f"[green]✓[/green] [orange1]{epub_out}[/orange1] written")
