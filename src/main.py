import logging
import src.pokemon
import src.epub
import argparse
from ebooklib import epub
from pathlib import Path
from rich.console import Console
from rich.logging import RichHandler


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ptoos-xray",
        description="Add Pokedex chapter to the PTOoS EPUB",
    )
    parser.add_argument(
        "input_epub", nargs="?", help="Specify PTOoS EPUB filename.", type=Path
    )
    parser.add_argument(
        "output_epub",
        nargs="?",
        help="Specify output filename or leave out to update input file.",
        type=Path,
    )
    parser.add_argument(
        "--pokemon_dir",
        help="Specify directory that contains Pokemon information and images.",
        default="pokemon",
        type=Path,
    )
    parser.add_argument(
        "--download",
        help="Download Pokemon information and images into Pokemon directory",
        action="store_true",
    )
    parser.add_argument(
        "--compress", help="Compress Pokemon images with pngquant.", action="store_true"
    )
    return parser


def init_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )


def write_epub(epub_with_pokedex: epub.EpubBook, epub_out: Path):
    console = Console()
    with console.status(f"Writing {epub_out}"):
        epub.write_epub(epub_out, epub_with_pokedex, {})
    console.print(f"[green]✓[/green] [orange1]{epub_out}[/orange1] written")


def main():
    init_logging()
    args = get_parser().parse_args()

    if args.download:
        src.pokemon.download_pokemon(args.pokemon_dir)

    if args.compress:
        src.pokemon.compress_pokemon_images(args.pokemon_dir)

    if args.input_epub:
        pokemon = src.pokemon.load_pokemon(args.pokemon_dir)
        output_epub = args.output_epub if args.output_epub else args.input_epub
        epub = src.epub.get_epub_with_pokedex(args.input_epub, pokemon)
        write_epub(epub, output_epub)
