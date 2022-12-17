import requests
import sys
import os
import logging
import shutil
import subprocess
import re
from pathlib import Path
from rich.progress import track
from pydantic import BaseModel
from bs4 import BeautifulSoup
from typing import List


ALL_POKEMON_JSON = Path("pokemon.json")
POKEDEX_HTML = Path("pokedex.html")
BULBAPEDIA_BASE_URL = "https://bulbapedia.bulbagarden.net"
NATIONAL_INDEX_SUFFIX = "/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number"
NATIONAL_INDEX_URL = BULBAPEDIA_BASE_URL + NATIONAL_INDEX_SUFFIX


class Pokemon(BaseModel):
    name: str
    link_id: str
    img_filename: Path
    description: str = ""
    appears_in_book: bool = False


class PokemonInProgress(BaseModel):
    name: str
    link_id: str
    index: str
    html_url: str
    html_filename: Path
    img_filename: Path
    description: str = ""
    appears_in_book: bool = False


class PokemonJson(BaseModel):
    pokemon: List[Pokemon]


def download_to_file(url: str, filename: Path):
    """Downloads url into filename."""
    if filename.is_file():
        logging.debug(f"'{filename}' exists.")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0"
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        logging.critical(f"Could not download '{filename}'.")
        sys.exit(1)

    # Works for text and images
    with open(filename, "wb") as f:
        for c in r:
            f.write(c)
    logging.debug(f"'{filename}' downloaded.")


def get_pokemon_table_row_soups(national_index_filename: Path) -> List[BeautifulSoup]:
    """Return a list of all Pokemon table rows on the National Index page"""
    with open(national_index_filename, "r") as r:
        soup = BeautifulSoup(r, "lxml")
    pokemon_list_soup = soup.find(
        id="List_of_Pokémon_by_National_Pokédex_number"
    ).parent
    generation_soups = pokemon_list_soup.find_next_siblings("h3")
    table_row_soups = []
    for generation_soup in generation_soups:
        tbody_soup = generation_soup.find_next("tbody")
        # skip first row because it is the header
        table_row_soups += tbody_soup.find_all("tr", recursive=False)[1:]
    return table_row_soups


def get_from_table_row(
    pokemon_dir: Path, table_row_soup: BeautifulSoup
) -> PokemonInProgress:
    """Extract Pokemon from a row in the National Index
    This  has broken and will break again when Bulbapedia updates their Pokedex HTML."""
    name = table_row_soup.find("a").attrs["title"]
    link_id = re.sub("[^a-z]", "", name.lower())
    index = table_row_soup.find("td").text.strip()
    html_url = BULBAPEDIA_BASE_URL + table_row_soup.find("a").attrs["href"]
    html_filename = os.path.join(pokemon_dir, name.lower() + ".html")
    img_filename = os.path.join(pokemon_dir, name.lower() + ".png")
    return PokemonInProgress(
        name=name,
        link_id=link_id,
        index=index,
        html_url=html_url,
        html_filename=html_filename,
        img_filename=img_filename,
    )


def load_pokemon(pokemon_dir: Path) -> List[Pokemon]:
    """Load Pokemon from JSON file Pokemon directory"""
    all_pokemon_json = os.path.join(pokemon_dir, ALL_POKEMON_JSON)
    try:
        pokemon = PokemonJson.parse_file(all_pokemon_json).pokemon
    except FileNotFoundError:
        logging.critical(
            f"Could not load '{all_pokemon_json}'. Download Pokemon first?"
        )
        sys.exit(1)
    return pokemon


def extract_pokemon_from_pokedex(pokemon_dir: Path) -> List[PokemonInProgress]:
    """Download Bulbapedia National Index and extract Pokemon from it"""
    national_index_filename = pokemon_dir / POKEDEX_HTML
    download_to_file(NATIONAL_INDEX_URL, national_index_filename)
    table_row_soups = get_pokemon_table_row_soups(national_index_filename)
    pokemon: List[PokemonInProgress] = []
    for table_row_soup in table_row_soups:
        p = get_from_table_row(pokemon_dir, table_row_soup)
        # Ignore Galarian and Alolan Pokemon (Pokemon with the same name)
        if pokemon and pokemon[-1].name == p.name:
            continue
        pokemon.append(p)
    return pokemon


def download_pokemon(pokemon_dir: Path):
    """Scrape Pokemon data and images from the Bulbapedia national dex"""
    os.makedirs(pokemon_dir, exist_ok=True)
    pokemon_in_progress: List[PokemonInProgress] = extract_pokemon_from_pokedex(
        pokemon_dir
    )
    pokemon: List[Pokemon] = []
    for p_in_progress in track(pokemon_in_progress, description="Download Pokemon"):
        extend_pokemon(p_in_progress)
        p = Pokemon(**p_in_progress.dict())
        pokemon.append(p)

    pokemon_json = PokemonJson(pokemon=pokemon)
    all_pokemon_json = os.path.join(pokemon_dir, ALL_POKEMON_JSON)
    with open(all_pokemon_json, "w") as f:
        f.write(pokemon_json.json(indent=2))


def extend_pokemon(p: PokemonInProgress):
    """Add description and download Pokemon image"""
    download_to_file(p.html_url, p.html_filename)
    with open(p.html_filename, "r") as r:
        soup = BeautifulSoup(r, "lxml")
    content_soup: BeautifulSoup = soup.find(id="mw-content-text").contents[0]

    if not p.description:
        p_soup = content_soup.find("p")
        description = []
        while p_soup.name == "p":
            description.append(p_soup.get_text())
            p_soup = p_soup.next_sibling
        p.description = "".join(description)

    if not p.img_filename.is_file():
        img_url = (
            content_soup.find("table")
            .find_next_sibling("table")
            .find("img")
            .attrs["src"]
        )
        img_url = img_url.replace("//", "https://")
        download_to_file(img_url, p.img_filename)


def compress_pokemon_images(pokemon_dir: Path):
    """Compress Pokemon images with pngquant for smaller epub size"""
    PNGQUANT = "pngquant"
    if shutil.which(PNGQUANT) is None:
        logging.critical(f"Compress requires '{PNGQUANT}' executable")
        sys.exit(1)

    def compress_image(img_filename: Path):
        args: List[str] = [
            PNGQUANT,
            str(img_filename),
            "--output",
            str(img_filename),
            "-f",
        ]
        subprocess.run(args)

    def compress_has_already_been_run(img_filename: Path) -> bool:
        size_before = os.path.getsize(img_filename)
        compress_image(img_filename)
        size_after = os.path.getsize(img_filename)
        return size_before == size_after

    pokemon = load_pokemon(pokemon_dir)
    if compress_has_already_been_run(pokemon[0].img_filename):
        logging.warning(
            f"Looks like '{pokemon[0].img_filename}' has already been compressed."
        )

    for p in track(pokemon, description="Compress Pokemon"):
        compress_image(p.img_filename)
