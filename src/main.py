import sys
import logging
import src.pokemon
import src.epub

from rich.logging import RichHandler


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler()],
    )
    try:
        ptoos_epub = sys.argv[1]
    except IndexError:
        ptoos_epub = "ptoos.epub"
    pokemon = src.pokemon.get_pokemon()
    src.epub.patch(ptoos_epub, pokemon)
