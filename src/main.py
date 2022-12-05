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
        handlers=[RichHandler(rich_tracebacks=True)],
    )
    try:
        ptoos_epub = sys.argv[1]
    except IndexError:
        ptoos_epub = "ptoos.epub"
        logging.warning(f"No epub file provided. Defaulting to '{ptoos_epub}'.")
    pokemon = src.pokemon.get_pokemon()
    # for p in pokemon:
    #     p.img_filename = p.img_filename.replace(".png", "-fs8.png")
    src.epub.patch(ptoos_epub, pokemon)
