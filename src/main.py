import logging
import src.pokemon
import src.epub


def init_logging():
    logging.basicConfig(level=logging.INFO)


def main():
    init_logging()
    pokemon = src.pokemon.get_pokemon()
    src.epub.patch("poos.epub", pokemon)
