import logging
import src.pokemon


def init_logging():
    logging.basicConfig(level=logging.DEBUG)


def main():
    init_logging()
    p = src.pokemon.get_pokemon()
