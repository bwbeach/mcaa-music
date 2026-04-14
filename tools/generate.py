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

VOICE_SONG_NOTES = {
    "Komo Mai Kau Mapuna Hoe" : {
        "All Voices" : "This is a recording from rehearsal on March 31, starting at measure 46."
    },
    "Ka Nohona Pili Kai": {
        "Alto 1" : "Recording from March 31 sectional",
        "Alto 2" : "Recording from March 31 sectional",
    },
    "Maikai Ka Makani o Kohala": {
        "Alto 1" : "Recording from March 31 sectional",
        "Alto 2" : "Recording from March 31 sectional",
    },
}


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


class VoicePart:
    """
    Constant structure that holds information about one voice part.

        pretty_name - The name to display to humans
        file_name - The name to use for files and in URL paths
            (same as pretty_name, but no spaces and all lower case)
        song_names - Possible names to use embedded in song file names

    The constructor accepts a primary song name, which is something like
    "Sop1".  It assumes there just one other name that could be used, and
    that it's made by dropping the final number.
    """
    def __init__(self, pretty_name, song_suffixes):
        self.pretty_name = pretty_name
        self.file_name = pretty_name.replace(" ", "").lower()
        self.song_suffixes = song_suffixes


VOICE_PARTS = [
    VoicePart("Soprano 1", ["SOP as sung at sectional", "SOPRANO on piano", "Sop1Dom", "SopDom", "Sop1aDom", "S1", "S1 S2", "SOP", "Bal"]),
    VoicePart("Soprano 2", ["SOP as sung at sectional", "SOPRANO on piano", "Sop2Dom", "SopDom", "Sop2aDom", "S2", "S1 S2", "SOP", "Bal"]),
    VoicePart("Alto 1", ["ALTO_sung", "ALTO on piano", "Alt1Dom", "AltDom", "A1", "ALTO", "Bal"]),
    VoicePart("Alto 2", ["ALTO_sung", "ALTO on piano", "Alt2Dom", "AltDom", "A2", "ALTO", "Bal"]),
    VoicePart("Tenor 1", ["TENOR on piano", "Ten1Dom", "TenDom", "T1", "TENOR", "Bal"]),
    VoicePart("Tenor 2", ["TENOR on piano", "Ten2Dom", "TenDom", "T2", "TENOR", "Bal"]),
    VoicePart("Bass 1", ["BASS on piano", "Bas1Dom", "BasDom", "B1", "B1 B2", "BASS", "Bal"]),
    VoicePart("Bass 2", ["BASS on piano", "Bas2Dom", "BasDom", "B2", "B1 B2", "BASS", "Bal"]),
    VoicePart("All Voices", ["Bal"]),
]


class Song:
    """
    Constant structure that holds a song's name and all of its music files.

        pretty_name - The name to display to humans.
    """
    def __init__(self, camel_case_name, music_files):
        self.camel_case_name = camel_case_name
        self.pretty_name = make_pretty_name(camel_case_name)
        self.file_name = camel_case_name.lower()
        self.music_files = music_files

    def html_file_name_for_part(self, voice_part):
        if self.music_file_name_for_part(voice_part):
            return f"{self.file_name}_{voice_part.file_name}.html"

    def music_path_name_for_part(self, voice_part):
        return self.music_file_name_for_part(voice_part)

    def music_file_name_for_part(self, voice_part):
        for suffix in voice_part.song_suffixes:
            for music_file in self.music_files:
                if (suffix + ".") in music_file:
                    return music_file
        if len(self.music_files) == 1:
            return self.music_files[0]
        return None


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
    song_names = sorted(song_data.keys())
    songs = [
        Song(song_name, song_data[song_name])
        for song_name in song_names
    ]

    # Definitions of variables used by templates
    template_data = dict(
        is_local=is_local,
        song_names=song_names,
    )

    pretty_voice_parts = list(
        voice_part.pretty_name
        for voice_part in VOICE_PARTS
    )
    pretty_songs = list(
        song.pretty_name
        for song in songs
    )
    for s, d in VOICE_SONG_NOTES.items():
        assert s in pretty_songs, f"song name in notes not found: {repr(s)}"
        for vp in d.keys():
            assert vp in pretty_voice_parts, f"voice part in notes not found: {repr(vp)}"

    # Generate voice part files
    notes_used = set()
    for voice_part in VOICE_PARTS:
        # Make the page that lists all of the songs for this voice part
        template = jinja2_env.get_template("voice_part.html")
        voice_data = dict(
            songs=songs,
            voice_part=voice_part,
        )
        render_template(jinja2_env, "voice_part.html", voice_data, os.path.join(output_dir, f"{voice_part.file_name}.html"))

        # Make one player page for each song
        if is_local:
            music_prefix = "file://" + os.path.abspath("music") + "/"
        else:
            music_prefix = "/music/"

        for song in songs:
            if song.html_file_name_for_part(voice_part):
                notes = VOICE_SONG_NOTES.get(song.pretty_name, {}).get(voice_part.pretty_name)
                if notes:
                    notes_used.add((song.pretty_name, voice_part.pretty_name))
                player_data = dict(
                    music_prefix=music_prefix,
                    voice_part=voice_part,
                    song=song,
                    notes=notes,
                )
                render_template(jinja2_env, "player.html", player_data, os.path.join(output_dir, song.html_file_name_for_part(voice_part)))

    all_notes = set(
        (song_name, voice_name)
        for song_name, voices in VOICE_SONG_NOTES.items()
        for voice_name in voices.keys()
    )
    unused_notes = all_notes - notes_used
    if unused_notes:
        print("Unused notes:", unused_notes)
        raise Exception("Some notes were unused")
        


if __name__ == "__main__":
    main()
