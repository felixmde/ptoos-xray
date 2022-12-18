import logging
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from ebooklib import epub
from src.pokemon import Pokemon
from typing import List, Dict, Optional, Set
from rich.progress import track

POKEMON_ID_PREFIX = "pokemon-id-"
POKEDEX_UID = "np_pokedex"
SPECIAL_CHARS_REGEX = re.compile("([:,.!?“”‘’… ]+)")


@dataclass
class AnnoyingPokemon:
    name_chunks: List[str]
    length_chunks: int
    name_in_pokedex: str


@dataclass
class ChapterContext:
    pokemon_lookup: Dict[str, Pokemon]
    pokemon_added: Set[str]  # Set to only link Pokemon for first occurrence in chapter
    chapter_soup: BeautifulSoup


ANNOYING_POKEMON = [
    AnnoyingPokemon(["mr", ". ", "mime"], 3, "mr. mime"),
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


def pokemon_to_link(p: Pokemon, name_as_in_book: str, ctx: ChapterContext) -> Tag:
    tag = ctx.chapter_soup.new_tag("a")
    tag.string = name_as_in_book
    tag.attrs["href"] = f"np_pokedex.xhtml#{POKEMON_ID_PREFIX}{p.link_id}"
    return tag


def is_annoying_pokemon(index: int, chunks: List[str]) -> Optional[AnnoyingPokemon]:
    for p in ANNOYING_POKEMON:
        if p.name_chunks == list(
            map(lambda s: s.lower(), chunks[index:index + p.length_chunks])
        ):
            return p
    return None


def patch_string(section: NavigableString, ctx: ChapterContext) -> List:
    """Replace Pokemon with link to Pokemon; requires splitting up the
    NavigableString into a list of NavigableStrings and Tags."""
    result: List[List] = [[]]
    index, chunks = 0, SPECIAL_CHARS_REGEX.split(str(section))
    while index < len(chunks):
        word = chunks[index]
        pokemon: Optional[Pokemon] = None
        increment: int = 1

        if word.lower() in ctx.pokemon_lookup:
            pokemon = ctx.pokemon_lookup[word.lower()]
        elif annoying_pokemon := is_annoying_pokemon(index, chunks):
            pokemon = ctx.pokemon_lookup[annoying_pokemon.name_in_pokedex]
            increment = annoying_pokemon.length_chunks

        if pokemon is not None and pokemon.name in ctx.pokemon_added:
            pokemon = None

        if pokemon is not None:
            ctx.pokemon_added.add(pokemon.name)
            pokemon.appears_in_book = True
            name = "".join(chunks[index:index + increment])
            link = pokemon_to_link(pokemon, name, ctx)
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


def patch_paragraph(paragraph: Tag, ctx: ChapterContext):
    contents = []
    for section in paragraph.contents:
        if isinstance(section, NavigableString):
            contents += patch_string(section, ctx)
        else:
            patch_paragraph(section, ctx)
            contents.append(section)
    paragraph.contents = contents


def patch_chapter(chapter_soup: BeautifulSoup, pokemon_lookup: Dict[str, Pokemon]) -> str:
    ctx = ChapterContext(
        pokemon_lookup=pokemon_lookup,
        pokemon_added=set(),
        chapter_soup=chapter_soup,
    )
    for p_soup in chapter_soup.find_all("p"):
        patch_paragraph(p_soup, ctx)
    return str(chapter_soup)


def get_pokemon_lookup(pokemon: List[Pokemon]) -> Dict[str, Pokemon]:
    pokemon_lookup = {p.name.lower(): p for p in pokemon}
    pokemon_lookup["nidoran"] = pokemon_lookup["nidoran♂"]
    pokemon_lookup["barrierd"] = pokemon_lookup["mr. mime"]
    return pokemon_lookup


def get_epub_with_pokedex(epub_filename: Path, pokemon: List[Pokemon]) -> epub.EpubBook:
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

    for chapter in track(chapters, description="Add Pokemon links to chapters"):
        chapter_soup = BeautifulSoup(chapter.content, "html.parser")
        chapter.content = patch_chapter(chapter_soup, pokemon_lookup)

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
            file_name=str(p.img_filename),
            media_type="image/png",
            content=image_content,
        )
        book.add_item(img)
    return book
