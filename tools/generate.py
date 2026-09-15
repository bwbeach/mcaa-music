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
import json
import os.path
import re
import sys

from jinja2 import Environment, FileSystemLoader, select_autoescape

_DISABLED = False

def clean_name(name: str) -> str:
    return "".join(c for c in name if c.isalnum())


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


SATB_PATTERN = re.compile(r"^(.*) S+A+T+B+$")

def make_pretty_name(name: str) -> str:
    """Convert a song folder name to a displayable name.

    >>> make_pretty_name("Coventry Carol SSAATTBB")
    'Coventry Carol'
    """
    m = SATB_PATTERN.match(name)
    if m:
        return m.group(1)
    else:
        return name


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

    @property
    def pretty_name(self) -> str:
        return make_pretty_name(self.name)

    def has_part(self, voice_part):
        return voice_part.key_name in self.info

    def html_file_name_for_part(self, voice_part):
        return f"{self.name}_{voice_part.key_name}.html"

    def music_path_name_for_part(self, voice_part, is_local):
        if voice_part.key_name not in self.info:
            raise ValueError(f"No part file for {voice_part} in: {self.name}")
        return self.info[voice_part.key_name]


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
    parser.add_argument("soli", help="JSON file with solo data")
    parser.add_argument("templates", help="Folder containing templates")
    parser.add_argument("output", help="Folder for generated files")
    parser.add_argument("--local", action="store_true", help="Use local paths")

    # Parse args
    args = parser.parse_args()
    song_data = read_json(args.songs)
    solo_to_file = read_json(args.soli)
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

    # What's the path to the music folder?
    if is_local:
        music_prefix = "file://" + os.path.abspath("to_upload") + "/"
    else:
        music_prefix = "/music/"

    # Generate voice part files
    for voice_part in VOICE_PARTS:
        # Make the page that lists all of the songs for this voice part
        voice_data = {
            "songs": songs,
            "voice_part": voice_part,
        }
        render_template(jinja2_env, "voice_part.html", voice_data, os.path.join(output_dir, f"{voice_part.key_name}.html"))

        # Make one player page for each song

        for song in songs:
            if song.html_file_name_for_part(voice_part):
                player_data = {
                    "player_title": song.pretty_name,
                    "player_subtitle": voice_part.pretty_name,
                    "notes": None,
                    "music_prefix": music_prefix,
                    "music_path_name": song.music_path_name_for_part(voice_part, is_local),
                    "back_name": voice_part.key_name,
                }
                render_template(jinja2_env, "player.html", player_data, os.path.join(output_dir, song.html_file_name_for_part(voice_part)))

    # Generate solo page
    solo_to_html = {
        solo_name: f"{clean_name(solo_name)}.html"
        for solo_name in solo_to_file
    }
    soli_data = {
        "solo_to_html": solo_to_html,
        "solo_titles": sorted(solo_to_file.keys()),
    }
    render_template(jinja2_env, "soli.html", soli_data, os.path.join(output_dir, "soli.html"))

    # Generate solo players
    for solo_name, solo_file in solo_to_file.items():
        player_data = {
            "player_title": solo_name,
            "player_subtitle": "",
            "notes": None,
            "music_prefix": music_prefix,
            "music_path_name": solo_file,
            "back_name": "soli",
        }
        html_file_name = solo_to_html[solo_name]
        render_template(jinja2_env, "player.html", player_data, os.path.join(output_dir, html_file_name))

if __name__ == "__main__":
    main()
