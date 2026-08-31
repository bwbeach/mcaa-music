#!/usr/bin/env -S uv run --python 3.14
# /// script
# dependencies = []
# ///

"""Converts track files into files to upload and list of songs/parts.

Input is the folder named `music`, which contains the AllFiles
directory synced down from Google Drive.  Each file is one track that
follows a naming convention, one of:

    <songName> - <part name> [Predominant|Muted] - <song info>.mp3
    <songName> - <part name> [1|2] [Predominant|Muted] - <song info>.mp3
    <songName> - Balanced Voices - <song info>.mp3
    <songName> - Accompaniment Track - <song info>.mp3

Links (hard links) the tracks into the director `to_upload`, with file
names cleaned up to exclude weird characters.

Writes `data/songs.json` with a mapping from song name to a map from
part name to file name.  For parts without a 1/2 split, both parts
link to the same file:

    {
        "Jingle Bells" : {
            "bass1" : "AllFiles/filename.mp3",
            "bass2" : "AllFiles/filename.mp3"
        }
    }
"""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

USAGE = """
Usage: organize.py

Reads from music/..., writes to to_upload/... and data/songs.json.
"""

MUSIC_FOLDER = "music"
TO_UPLOAD_FOLDER = "to_upload"

def usage():
    print(USAGE, file=sys.stderr)
    sys.exit(1)


def clean_file_name(fn: str) -> str:
    """Removes all non-alpha-numeric characters from the string, except for the '.' in 'mp3'

    >>> clean_file_name("A B.C.mp3")
    'ABC.mp3'
    >>> clean_file_name("foo.bar.mp3")
    'foobar.mp3'
    """
    if not fn.endswith(".mp3"):
        raise ValueError(f"keys must end with .mp3: {fn}")
    return "".join(c for c in fn[:-4] if c.isalnum()) + ".mp3"


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
        song, part_info, _ = m1.groups()
        song_file = f"AllFiles/{file.name}"

        
        if part_info == "Balanced Voices":
            yield song, "balancedvoices", song_file
        elif part_info == "Accompaniment Track":
            pass
        else:
            m2 = part_pattern.match(part_info.lower())
            if not m2:
                raise ValueError(f"Do not understand part info: {part_info!r}")
            part, high_low, volume = m2.groups()
            if volume == "muted" or volume == "descant" or part == "solo":
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


def recursive_delete(p: Path):
    if p.is_dir():
        for sub in p.iterdir():
            recursive_delete(sub)
        p.rmdir()
    elif p.is_file():
        p.unlink()
    else:
        raise ValueError(f"not a file or directory: {p}")


def main():
    if len(sys.argv) != 1:
        usage()
        
    music_folder = Path(MUSIC_FOLDER)
    all_files_folder = music_folder.joinpath("AllFiles")
    to_upload_folder = Path(TO_UPLOAD_FOLDER)
    
    if not all_files_folder.is_dir():
        print(f"'{all_files_folder}' is not a directory", file=sys.stderr())
        sys.exit(1)

    if to_upload_folder.exists():
        recursive_delete(to_upload_folder)
    to_upload_folder.mkdir()

    song_to_parts = defaultdict(dict)
    for song, part, file_name in get_song_triples(all_files_folder):
        clean_name = clean_file_name(file_name)
        song_to_parts[song][part] = clean_name

        link_dst = music_folder.joinpath(file_name)
        assert link_dst.is_file()
        link_src = to_upload_folder.joinpath(clean_name)

        if not link_src.exists():
            link_src.hardlink_to(link_dst)
            print(f"linked {link_src}")

    with open("data/songs.json", "w") as f:
        print(json.dumps(song_to_parts, sort_keys=True, indent=2), file=f)
    print("wrote data/songs.json")


if __name__ == "__main__":
    main()

