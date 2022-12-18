import epub
import src.pokemon as pokemon
from typing import List
from bs4 import BeautifulSoup


def test_patch_chapter_tauros():
    pokemon_lookup = epub.get_pokemon_lookup(get_pokemon())
    chapter_soup = BeautifulSoup("<p>it's a tauros yeah</p>", "lxml")
    o = epub.patch_chapter(chapter_soup, pokemon_lookup)
    e = s('<p>it\'s a <a href="np_pokedex.xhtml#pokemon-id-tauros">tauros</a> yeah</p>')
    assert o == e


def test_patch_chapter_double_tauros():
    pokemon_lookup = epub.get_pokemon_lookup(get_pokemon())
    chapter_soup = BeautifulSoup("<p>it's two tauros tauros</p>", "lxml")
    o = epub.patch_chapter(chapter_soup, pokemon_lookup)
    e = s('<p>it\'s two <a href="np_pokedex.xhtml#pokemon-id-tauros">tauros</a> tauros</p>')
    assert o == e


def test_patch_chapter_tauros_italic():
    pokemon_lookup = epub.get_pokemon_lookup(get_pokemon())
    chapter_soup = BeautifulSoup("<p>it's two <i>tauros</i> tauros</p>", "lxml")
    o = epub.patch_chapter(chapter_soup, pokemon_lookup)
    e = s('<p>it\'s two <i><a href="np_pokedex.xhtml#pokemon-id-tauros">tauros</a></i> tauros</p>')
    assert o == e


def test_patch_chapter_nidoran_with_s():
    pokemon_lookup = epub.get_pokemon_lookup(get_pokemon())
    chapter_soup = BeautifulSoup("<p>it's a Nidoran‘s goldfish</p>", "lxml")
    o = epub.patch_chapter(chapter_soup, pokemon_lookup)
    e = s('<p>it\'s a <a href="np_pokedex.xhtml#pokemon-id-nidoran">Nidoran</a>‘s goldfish</p>')
    assert o == e


def test_patch_chapter_nidoran_with_double_quotes():
    pokemon_lookup = epub.get_pokemon_lookup(get_pokemon())
    chapter_soup = BeautifulSoup("<p>it's a “Nidoran” duh</p>", "lxml")
    o = epub.patch_chapter(chapter_soup, pokemon_lookup)
    e = s('<p>it\'s a “<a href="np_pokedex.xhtml#pokemon-id-nidoran">Nidoran</a>” duh</p>')
    assert o == e


def test_patch_chapter_mr_mime():
    pokemon_lookup = epub.get_pokemon_lookup(get_pokemon())
    chapter_soup = BeautifulSoup("<p>it's a “Mr. Mime” duh</p>", "lxml")
    o = epub.patch_chapter(chapter_soup, pokemon_lookup)
    e = s('<p>it\'s a “<a href="np_pokedex.xhtml#pokemon-id-mrmime">Mr. Mime</a>” duh</p>')
    assert o == e


def test_patch_chapter_barrierd():
    pokemon_lookup = epub.get_pokemon_lookup(get_pokemon())
    chapter_soup = BeautifulSoup("<p>it's a “barrierd” duh</p>", "lxml")
    o = epub.patch_chapter(chapter_soup, pokemon_lookup)
    e = s('<p>it\'s a “<a href="np_pokedex.xhtml#pokemon-id-mrmime">barrierd</a>” duh</p>')
    assert o == e


def test_patch_chapter_farfetched():
    pokemon_lookup = epub.get_pokemon_lookup(get_pokemon())
    chapter_soup = BeautifulSoup("<p>it's a farfetch’d yo</p>", "lxml")
    o = epub.patch_chapter(chapter_soup, pokemon_lookup)
    e = s('<p>it\'s a <a href="np_pokedex.xhtml#pokemon-id-farfetchd">farfetch’d</a> yo</p>')
    assert o == e


def s(s: str) -> str:
    return "<html><body>" + s + "</body></html>"


def get_pokemon() -> List[pokemon.Pokemon]:
    return [
        pokemon.Pokemon(
            name="Tauros",
            link_id="tauros",
            img_filename="pokemon/tauros.png",
            description="Tauros (",
            appears_in_book=False),
        pokemon.Pokemon(
            name="Nidoran♂",
            link_id="nidoran",
            img_filename="pokemon.png",
            description="Nidoran",
            appears_in_book=False
        ),
        pokemon.Pokemon(
            name="Mr. Mime",
            link_id="mrmime",
            img_filename="pokemon/mr. mime.png",
            description="Mr. Mime",
            appears_in_book=False
        ),
        pokemon.Pokemon(
            name="Farfetch'd",
            link_id="farfetchd",
            img_filename="pokemon/farfetch'd.png",
            description="Farfetch",
            appears_in_book=False
        )
    ]
