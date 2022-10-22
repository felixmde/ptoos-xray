import ebooklib
import logging
from ebooklib import epub
from src.pokemon import Pokemon
from typing import List

POKEMON_ID_PREFIX = "pokemon-id-"

def create_pokedex_chapter(pokemon: List[Pokemon]) -> epub.EpubHtml:
    POKEDEX_TITLE = "Pokedex"
    POKEDEX_FILE = "content/np_pokedex.xhtml"
    POKEDEX_UID = "np_pokedex"
    chapter = epub.EpubHtml(title=POKEDEX_TITLE, file_name=POKEDEX_FILE, uid=POKEDEX_UID)
    content = ['<h1>Pokedex</h1>']

    for p in pokemon:
        content.append(f'<h2 id="{POKEMON_ID_PREFIX}{p.name.lower()}">{p.name}</h2>')
        content.append(f'  <p><img alt="[Pokemon {p.name}]" src="../{p.img_filepath}"/><br/></p>')
        content.append(f'  <p>{p.description}</p>')
        content.append('')

    chapter.content = "\n".join(content)
    return chapter

def patch(epub_filepath: str, pokemon: List[Pokemon]):
    book = epub.read_epub(epub_filepath)

    chapter = create_pokedex_chapter(pokemon)
    book.add_item(chapter)
    link = epub.Link(chapter.file_name, chapter.title, chapter.id)
    book.toc.append(link)
    book.spine.append((chapter.id, 'yes'))

    for p in pokemon:
        image_content = open(p.img_filepath, 'rb').read()
        img = epub.EpubItem(uid=p.name, file_name=p.img_filepath, media_type='image/png', content=image_content)
        book.add_item(img)

    # Link to Pokemon looks like this:
    # <a href="np_pokedex.xhtml#pokemon-id-bulbasaur">Bulbasaur!</a>

    epub.write_epub('tmp/test.epub', book, {})
    logging.info("Written")
