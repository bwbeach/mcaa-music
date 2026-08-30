#!/usr/bin/env -S uv run --python 3.14
# /// script
# dependencies = ["Jinja2"]
# ///
"""
Generates the mcaa-music website.  Inputs are:

    songs.json - List of song folder names and m3 file names.
    templates - Folder containing jinja2 templates for the files to generate.
    output - Folder to put generated files into.
"""

import argparse
import jinja2
import json
import os.path
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

_DISABLED = False

def camel_case_to_words(camel_case):
    """Convert a camel-case string into a list of words.

    >>> camel_case_to_words("TheRoadHome")
    ['The', 'Road', 'Home']
    >>> camel_case_to_words("AH5_TogetherOnThePorch")
    ['A', 'H', '5', 'Together', 'On', 'The', 'Porch']
    >>> camel_case_to_words("Komo Mai")
    ['Komo', 'Mai']
    """
    result = []
    current_word = []
    for c in camel_case:
        if c in "_":
            continue
        if (c.isupper() or c.isnumeric() or c.isspace()) and 0 < len(current_word):
            result.append("".join(current_word))
            current_word = []
        if not c.isspace():
            current_word.append(c)
    if 0 < len(current_word):
        result.append("".join(current_word))
    return result


def make_pretty_name(camel_case_name):
    """Convert a song folder name to a displayable name.

    >>> make_pretty_name("TheRoadHome")
    'The Road Home'
    >>> make_pretty_name("AH2_NewRoof")
    'At Home 2: New Roof'
    """
    if camel_case_name.startswith("AH"):
        num = camel_case_name[2]
        rest = " ".join(camel_case_to_words(camel_case_name[4:]))
        return f"At Home {num}: {rest}"
    else:
        return " ".join(camel_case_to_words(camel_case_name))


def clean_key(k: str) -> str:
    """Removes all non-alpha-numeric characters from the string, except for the '.' in 'mp3'

    >>> clean_key("A B.C.mp3")
    'ABC.mp3'
    >>> clean_key("foo.bar.mp3")
    'foobar.mp3'
    """
    if not k.endswith(".mp3"):
        raise ValueError(f"keys must end with .mp3: {k}")
    return "".join(c for c in k[:-4] if c.isalnum()) + ".mp3"


class VoicePart:
    """
    Constant structure that holds information about one voice part.

        pretty_name - The name to display to humans
        key_name - The key in the mapping
    """
    def __init__(self, pretty_name):
        self.pretty_name = pretty_name
        self.key_name = pretty_name.lower().replace(" ", "")

    def __repr__(self):
        return self.key_name


VOICE_PARTS = [
    VoicePart("Soprano 1"),
    VoicePart("Soprano 2"),
    VoicePart("Alto 1"),
    VoicePart("Alto 2"),
    VoicePart("Tenor 1"),
    VoicePart("Tenor 2"),
    VoicePart("Bass 1"),
    VoicePart("Bass 2"),
    VoicePart("Balanced Voices"),
]


class Song:
    """
    Constant structure that holds a song's name and all of its music files.

        pretty_name - The name to display to humans.
    """
    def __init__(self, name, song_info):
        self.name = name
        self.info = song_info

    def has_part(self, voice_part):
        return voice_part.key_name in self.info

    def html_file_name_for_part(self, voice_part):
        return f"{self.name}_{voice_part.key_name}.html"

    def music_path_name_for_part(self, voice_part, is_local):
        if voice_part.key_name not in self.info:
            raise ValueError(f"No part file for {voice_part} in: {self.name}")
        file_name = self.info[voice_part.key_name]
        if is_local:
            return file_name
        else:
            return clean_key(file_name)


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.loads(f.read())


def render_template(jinja2_env, template_name, data, output_file):
    template = jinja2_env.get_template(template_name)
    rendered = template.render(**data)
    with open(output_file, "w") as f:
        f.write(rendered)
    print("wrote:", output_file)


def main():
    # Make arg parser
    parser = argparse.ArgumentParser()
    parser.add_argument("songs", help="JSON file with song data")
    parser.add_argument("templates", help="Folder containing templates")
    parser.add_argument("output", help="Folder for generated files")
    parser.add_argument("--local", action="store_true", help="Use local paths")

    # Parse args
    args = parser.parse_args()
    song_data = read_json(args.songs)
    template_loader = FileSystemLoader(args.templates)
    output_dir = args.output
    is_local = args.local

    # Validate args
    if not os.path.isdir(output_dir):
        print(f"'{output_dir}' is not a directory", file=sys.stderr)
        sys.exit(1)

    # Set up template generation
    jinja2_env = Environment(
        loader=template_loader,
        autoescape=select_autoescape()
    )

    # Make the list of songs
    songs = sorted(
        (
            Song(song_name, song_info)
            for song_name, song_info in song_data.items()
        ),
        key=lambda s: s.name
    )

    # Definitions of variables used by templates
    template_data = dict(
        is_local=is_local,
        songs=songs,
    )

    # Generate voice part files
    for voice_part in VOICE_PARTS:
        # Make the page that lists all of the songs for this voice part
        template = jinja2_env.get_template("voice_part.html")
        voice_data = dict(
            songs=songs,
            voice_part=voice_part,
        )
        render_template(jinja2_env, "voice_part.html", voice_data, os.path.join(output_dir, f"{voice_part.key_name}.html"))

        # Make one player page for each song
        if is_local:
            music_prefix = "file://" + os.path.abspath("music") + "/"
        else:
            music_prefix = "/music/"

        for song in songs:
            if song.html_file_name_for_part(voice_part):
                player_data = dict(
                    music_prefix=music_prefix,
                    voice_part=voice_part,
                    song=song,
                    is_local=is_local,
                )
                render_template(jinja2_env, "player.html", player_data, os.path.join(output_dir, song.html_file_name_for_part(voice_part)))


if __name__ == "__main__":
    main()
