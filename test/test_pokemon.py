import pokemon


def test_extract_pokemon_from_pokdex(tmp_path):
    pokemon_list = pokemon.extract_pokemon_from_pokedex(tmp_path)
    assert len(pokemon_list) == 1008


def test_get_pokemon_from_table_row(tmp_path):
    pokemon_list = pokemon.extract_pokemon_from_pokedex(tmp_path)
    p = pokemon_list[36]
    assert p.name == "Vulpix"
    assert p.link_id == "vulpix"
    assert p.index == "#037"
    assert p.html_url == "https://bulbapedia.bulbagarden.net/wiki/Vulpix_(Pok%C3%A9mon)"
    assert str(p.html_filename).endswith("vulpix.html")
    assert str(p.img_filename).endswith("vulpix.png")
    assert p.description == ""


def test_extend_pokemon(tmp_path):
    pokemon_list = pokemon.extract_pokemon_from_pokedex(tmp_path)
    p = pokemon_list[36]
    p.img_filename = tmp_path / "vulpix.png"
    pokemon.extend_pokemon(p)
    assert p.img_filename.is_file()
    assert p.description.startswith("Vulpix (Japanese: \u30ed\u30b3\u30f3 Rokon)")
