# ptoos-xray

Script that annotates the Pokemon: the Origin of the Species e-book with links
to descriptions and pictures of the Pokemon within the e-book itself. 

It works with the epub that you can download from [Daystar Eld's Patreon](https://www.patreon.com/daystareld/).

## Usage

```shell
pip install --user pipenv
pipenv install
pipenv shell
python ptoos-xray.py "DaystarEld - Pokemon The Origin of Species.epub"
```

## Run tests

```shell
pipenv install --dev
pipenv run pytest
```

## Compress Pokemon PNGs

Use `pngquant` to compress the PNGs and get a smaller epub file.

## Credits

Full credit for the Pokemon names, images, and descriptions goes to
[Bulbapedia](https://bulbapedia.bulbagarden.net) under
[Attribution-NonCommercial-ShareAlike 2.5](https://creativecommons.org/licenses/by-nc-sa/2.5/).
