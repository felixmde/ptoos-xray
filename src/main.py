import sys
import logging
import src.pokemon
import src.epub


def main():
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    try:
        ptoos_epub = sys.argv[1]
    except IndexError:
        ptoos_epub = "poos.epub"
    logging.info(f"Patching '{ptoos_epub}'.")
    pokemon = src.pokemon.get_pokemon()
    src.epub.patch(ptoos_epub, pokemon)
