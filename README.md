# ptoos-xray

Script that adds a Pokedex chapter to the *Pokemon: Origin of the Species* epub
and links Pokemon to the respective section in that chapter.

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

## Pokemon download and compression

The Pokemon information and pictures are part of the repository.

To redownload the data delete the contents of the `pokemon` directory and run
the script with the `--download` flag. This takes a while which is why I decided
that checking in the data is a good idea.

Install `pngquant` to compress the PNGs and get a smaller epub file. Thanks to 
C0rn3j for suggesting that. The images are checked in in their compressed form.

## Credits

Full credit for the Pokemon names, images, and descriptions goes to
[Bulbapedia](https://bulbapedia.bulbagarden.net) under
[Attribution-NonCommercial-ShareAlike 2.5](https://creativecommons.org/licenses/by-nc-sa/2.5/).
