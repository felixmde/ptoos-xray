import requests
import sys
import os
import logging
import re
from rich.progress import track
from pydantic import BaseModel
from bs4 import BeautifulSoup
from typing import List


POKEMON_CACHE_DIRECTORY = "pokemon"
BULBAPEDIA_BASE_URL = "https://bulbapedia.bulbagarden.net"
NATIONAL_INDEX_URL = (
    BULBAPEDIA_BASE_URL + "/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number"
)


class Pokemon(BaseModel):
    name: str
    link_id: str
    index: str
    html_url: str
    img_url: str
    html_filename: str
    img_filename: str
    json_filename: str
    description: str = ""
    appears_in_book: bool = False


def download_to_file(url: str, filename: str, override=False):
    """Downloads url into filename."""
    if os.path.isfile(filename) and override is False:
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


def download_national_index_html(national_index_filename: str):
    download_to_file(NATIONAL_INDEX_URL, national_index_filename)


def get_pokemon_table_row_soups(national_index_filename: str) -> List[BeautifulSoup]:
    with open(national_index_filename, "r") as r:
        soup = BeautifulSoup(r, "html.parser")
    pokemon_list_soup = soup.find(
        id="List_of_Pokémon_by_National_Pokédex_number"
    ).parent
    generation_soups = pokemon_list_soup.find_next_siblings("h3")
    table_row_soups = []
    for generation_soup in generation_soups:
        table_soup = generation_soup.find_next_sibling("table")
        tbody_soup = generation_soup.find_next("tbody")
        # skip first row because it is the header
        table_row_soups += tbody_soup.find_all("tr", recursive=False)[1:]
    return table_row_soups


def extract_pokemon_from_table_row(table_row_soup: BeautifulSoup) -> Pokemon:
    name = table_row_soup.find_next("th").next_element.attrs["title"]
    link_id = re.sub("[^a-z]", "", name.lower())

    # load Pokemon from JSON if it already exists
    json_filename = os.path.join(POKEMON_CACHE_DIRECTORY, name.lower() + ".json")
    if os.path.isfile(json_filename):
        p = Pokemon.parse_file(json_filename)
        logging.debug(f"Loaded '{p.json_filename}'.")
        return p

    index = table_row_soup.find_next("td").next_sibling.next_sibling.text.strip()
    html_url = (
        BULBAPEDIA_BASE_URL + table_row_soup.find_next("th").next_element.attrs["href"]
    )
    img_url = table_row_soup.find("img").attrs["src"]
    html_filename = os.path.join(POKEMON_CACHE_DIRECTORY, name.lower() + ".html")
    img_filename = os.path.join(POKEMON_CACHE_DIRECTORY, name.lower() + ".png")
    return Pokemon(
        name=name,
        link_id=link_id,
        index=index,
        html_url=html_url,
        img_url=img_url,
        html_filename=html_filename,
        img_filename=img_filename,
        json_filename=json_filename,
    )


def get_pokemon() -> List[Pokemon]:
    """Scrape Pokemon from the Bulbapedia national dex"""
    if not os.path.isdir(POKEMON_CACHE_DIRECTORY):
        os.mkdir(POKEMON_CACHE_DIRECTORY)
    national_index_filename = os.path.join(POKEMON_CACHE_DIRECTORY, "pokedex.html")
    download_national_index_html(national_index_filename)
    table_row_soups = get_pokemon_table_row_soups(national_index_filename)

    pokemon = []
    for table_row_soup in track(table_row_soups, description="Download Pokemon"):
        p = extract_pokemon_from_table_row(table_row_soup)

        # Ignore Galarian and Alolan Pokemon (Pokemon with the same name)
        if pokemon and pokemon[-1].name == p.name:
            continue
        pokemon.append(p)

        # Pokemon has already been downloaded
        if p.description and os.path.isfile(p.img_filename):
            continue

        extend_pokemon(p)
        with open(p.json_filename, "w") as f:
            f.write(p.json())
            logging.debug(f"Saved {p.json_filename}.")

    # Filter out speculative Pokemon
    pokemon = [
        p
        for p in pokemon
        if not p.description.startswith("This article's contents will change")
    ]

    return pokemon


def extend_pokemon(p: Pokemon):
    """Add description and download Pokemon image"""
    download_to_file(p.html_url, p.html_filename)
    with open(p.html_filename, "r") as r:
        soup = BeautifulSoup(r, "html.parser")
    content_soup: BeautifulSoup = soup.find(id="mw-content-text").contents[0]

    if not p.description:
        p_soup = content_soup.find("p")
        description = []
        while p_soup.name == "p":
            description.append(p_soup.get_text())
            p_soup = p_soup.next_sibling
        p.description = "".join(description)

    if not os.path.isfile(p.img_filename):
        img_url = (
            content_soup.find("table")
            .find_next_sibling("table")
            .find("img")
            .attrs["src"]
        )
        img_url = img_url.replace("//", "https://")
        p.img_url = img_url
        download_to_file(img_url, p.img_filename)
