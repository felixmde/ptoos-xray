import pokemon 
import os
import filecmp


def test_download_national_index_html(tmp_path):
    pokemon_html = tmp_path / "pokedex.html"
    pokemon.download_national_index_html(pokemon_html)
    assert os.path.getsize(pokemon_html) > 500000

def test_get_pokemon_table_row_soups():
    national_index = "test/test_pokedex.html"
    row_soups = pokemon.get_pokemon_table_row_soups(national_index) 
    assert len(row_soups) == 994

def test_extract_pokemon_from_table_row(tmp_path):
    national_index = "test/test_pokedex.html"
    pokemon.POKEMON_CACHE_DIRECTORY = tmp_path
    row_soups = pokemon.get_pokemon_table_row_soups(national_index) 
    p = pokemon.extract_pokemon_from_table_row(row_soups[42])
    assert p.name == 'Vulpix'
    assert p.index == '#037'
    assert p.html_url == 'https://bulbapedia.bulbagarden.net/wiki/Vulpix_(Pok%C3%A9mon)'
    assert p.img_url == '//archives.bulbagarden.net/media/upload/thumb/3/35/037Vulpix-Alola.png/70px-037Vulpix-Alola.png'
    assert p.img_filename.endswith('vulpix.png')
    assert p.json_filename.endswith('vulpix.json')
    assert p.description == ''
    assert p.appears_in_book == False

def test_extend_pokemon(tmp_path):
    national_index = "test/test_pokedex.html"
    row_soups = pokemon.get_pokemon_table_row_soups(national_index) 
    p = pokemon.extract_pokemon_from_table_row(row_soups[42])
    p.img_filename = tmp_path / 'vulpix.png'
    pokemon.extend_pokemon(p)
    assert filecmp.cmp(p.img_filename, 'test/test_vulpix.png')
    assert p.description.startswith("Vulpix (Japanese: \u30ed\u30b3\u30f3 Rokon)")