#!/usr/bin/env -S uv run --python 3.14

"""Generates songs.json

The `music` folder named on the command line is expected to hold
an AllFiles directory that holds all of the songs, with names
following a naming convention.  Each song is named like one of these

    <songName> - <part name> [Predominant|Muted] - <song info>.mp3
    <songName> - <part name> [1|2] [Predominant|Muted] - <song info>.mp3
    <songName> - Balanced Voices - <song info>.mp3
    <songName> - Accompaniment Track - <song info>.mp3

The result is a JSON file, mapping song name to: map from part name to
file name, like this:

    {
        "Jingle Bells" : {
            "Bass 1" : "AllFiles/filename.mp3"
        }
    }

For parts without a 1/2 split, both parts will be listed with the same file:

    {
        "Jingle Bells" : {
            "Bass 1" : "AllFiles/filename.mp3",
            "Bass 2" : "AllFiles/filename.mp3"
        }
    }
"""

import json
import re
import sys

from collections import defaultdict
from pathlib import Path


USAGE = """
Usage: get_names.py <musicFolder>

Assumes that the music folder contains AllFiles/
"""

def usage():
    print(USAGE, file=sys.stderr)
    sys.exit(1)


def get_song_triples(all_files_folder):
    """Yields (song, part, file) triples.
    """
    top_pattern = re.compile("^([^-]*) - ([^-]*) - ([^-]*).mp3$")
    part_pattern = re.compile("^(alto|bass|tenor|soprano|descant|solo) (1 |2 |3 |solo |)(muted|predominant)$")
    
    for file in all_files_folder.iterdir():
        if file.suffix != ".mp3":
            raise ValueError(f"File name suffix ({file.suffix}) is not mp3: {file}")

        m1 = top_pattern.match(file.name)
        if not m1:
            raise ValueError(f"File name does not match top pattern: {file}")
        song, part_info, song_info = m1.groups()
        song_file = f"AllFiles/{song}"

        
        if part_info == "Balanced Voices":
            yield song, "balanced", song_file
        elif part_info == "Accompaniment Track":
            pass
        else:
            m2 = part_pattern.match(part_info.lower())
            if not m2:
                raise ValueError(f"Do not understand part info: {part_info!r}")
            part, high_low, volume = m2.groups()
            if volume == "muted":
                pass
            elif part == "descant":
                pass
            elif part == "solo":
                pass
            elif volume == "predominant":
                if high_low == "1 ":
                    yield song, part + "1", song_file
                elif high_low == "2 ":
                    yield song, part + "2", song_file
                elif high_low == "":
                    yield song, part + "1", song_file
                    yield song, part + "2", song_file
                elif high_low == "solo ":
                    pass
                else:
                    raise ValueError(f"Do not understand part info (high_low): {part_info!r}")
            else:
                raise ValueError(f"Do not understand part info (volume): {part_info!r}")
            

def main():
    if len(sys.argv) != 2:
        usage()
        
    music_folder = Path(sys.argv[1])
    all_files_folder = music_folder.joinpath("AllFiles")
    
    if not all_files_folder.is_dir():
        print(f"'{all_files_folder}' is not a directory", file=sys.stderr())
        sys.exit(1)

    song_to_parts = defaultdict(dict)
    for song, part, file in get_song_triples(all_files_folder):
        song_to_parts[song][part] = file

    print(json.dumps(song_to_parts, sort_keys=True, indent=2))
        
    
if __name__ == "__main__":
    main()
