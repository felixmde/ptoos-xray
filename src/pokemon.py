import requests
import sys
import os
import logging
from pydantic import BaseModel
from bs4 import BeautifulSoup
from typing import List


POKEMON_CACHE_DIRECTORY = "pokemon"
BULBAPEDIA_BASE_URL = "https://bulbapedia.bulbagarden.net"
NATIONAL_INDEX_URL = BULBAPEDIA_BASE_URL + "/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number"


class Pokemon(BaseModel):
    name: str
    index: str
    html_url: str
    img_url: str
    html_filepath: str
    img_filepath: str
    json_filepath: str
    description: str = ""


def download_to_file(url: str, filepath: str, override=False):
    """ Downloads url into filepath. """
    if os.path.isfile(filepath) and override is False:
        logging.debug(f"'{filepath}' exists.")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
    }
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        logging.warning(f"Could not download '{filepath}'")
        return

    # Works for text and images
    with open(filepath, "wb") as f:
        for c in r:
            f.write(c)
    logging.debug(f"'{filepath}' downloaded.")


def get_pokemon() -> List[Pokemon]:
    """ Scrape Pokemon from the Bulbapedia national dex """
    NATIONAL_INDEX_FILEPATH = os.path.join(POKEMON_CACHE_DIRECTORY, "pokedex.html")
    download_to_file(NATIONAL_INDEX_URL, NATIONAL_INDEX_FILEPATH)
    with open(NATIONAL_INDEX_FILEPATH, "r") as r:
        soup = BeautifulSoup(r, "html.parser")
    pokemon_list_soup: BeautifulSoup = soup.find(id="List_of_Pokémon_by_National_Pokédex_number").parent
    generation_soups: BeautifulSoup = pokemon_list_soup.find_next_siblings("h3")

    table_row_soups = []
    for generation_soup in generation_soups:
        table_soup: BeautifulSoup = generation_soup.find_next_sibling("table")
        tbody_soup: BeautifulSoup = generation_soup.find_next("tbody")
        # skip first row because it is the header
        table_row_soups += tbody_soup.find_all("tr", recursive=False)[1:]

    pokemon = []
    for table_row_soup in table_row_soups:
        name = table_row_soup.find_next("th").next_element.attrs["title"]

        # ignore Galarian and Alolan Pokemon so
        if pokemon and pokemon[-1].name == name:
            continue

        # load Pokemon from JSON if it already exists
        json_filepath = os.path.join(POKEMON_CACHE_DIRECTORY, name.lower() + ".json")
        if os.path.isfile(json_filepath):
            p = Pokemon.parse_file(json_filepath)
            pokemon.append(p)
            logging.debug(f"Loaded {p.json_filepath}.")
            continue

        index = table_row_soup.find_next("td").next_sibling.next_sibling.text.strip()
        html_url = BULBAPEDIA_BASE_URL + table_row_soup.find_next("th").next_element.attrs["href"]
        img_url = table_row_soup.find("img").attrs["src"]
        html_filepath = os.path.join(POKEMON_CACHE_DIRECTORY, name.lower() + ".html")
        img_filepath = os.path.join(POKEMON_CACHE_DIRECTORY, name.lower() + ".png")
        p = Pokemon(name=name,
                    index=index,
                    html_url=html_url,
                    img_url=img_url,
                    html_filepath=html_filepath,
                    img_filepath=img_filepath,
                    json_filepath=json_filepath)
        pokemon.append(p)
        extend_pokemon(p)
        with open(p.json_filepath, 'w') as f:
            f.write(p.json())
            logging.info(f"Saved {p.json_filepath}.")

    # Filter out speculative Pokemon
    pokemon = [p for p in pokemon if not p.description.startswith("This article's contents will change")]

    logging.info("Pokemon loaded.")
    return pokemon


def extend_pokemon(p: Pokemon):
    """ Add description and download Pokemon image """
    download_to_file(p.html_url, p.html_filepath)
    with open(p.html_filepath, "r") as r:
        soup = BeautifulSoup(r, "html.parser")
    content_soup: BeautifulSoup = soup.find(id='mw-content-text').contents[0]

    # description
    p_soup = content_soup.find("p")
    description = []
    while p_soup.name == 'p':
        description.append(p_soup.get_text())
        p_soup = p_soup.next_sibling
    p.description = "".join(description)

    # image
    img_url = content_soup.find("table").find_next_sibling("table").find("img").attrs["src"]
    img_url = img_url.replace("//", "https://")
    p.img_url = img_url
    download_to_file(img_url, p.img_filepath)

