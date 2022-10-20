import requests
import sys
from bs4 import BeautifulSoup
from typing import List

POKEMON_FILE = "pokemon/pokedex.html"
POKEMON_URL = "https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_National_Pok%C3%A9dex_number"


def get_pokedex():
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
    }
    r = requests.get(POKEMON_URL, headers=headers)
    with open(POKEMON_FILE, "w") as f:
        f.write(r.text)

def pokemon_for_generation_soup(generation_soup: BeautifulSoup):
    print(generation_soup)
    table_soup: BeautifulSoup = generation_soup.find_next_sibling("table")
    tbody_soup: BeautifulSoup = generation_soup.find_next("tbody")
    table_row_soups: List[BeautifulSoup()] = tbody_soup.find_all_next("tr")
    for table_row_soup in table_row_soups:
        print(table_row_soup.find_next("th").next_element.attrs["title"])
    sys.exit(0)
    return tbody_soup

def main():
    with open(POKEMON_FILE, "r") as r:
        soup = BeautifulSoup(r, "html.parser")
    pokemon_list_soup: BeautifulSoup = soup.find(id="List_of_Pokémon_by_National_Pokédex_number").parent
    generation_soups: BeautifulSoup = pokemon_list_soup.find_next_siblings("h3")[0:1]
    pokemon = map(pokemon_for_generation_soup, generation_soups)
    print(list(pokemon))
