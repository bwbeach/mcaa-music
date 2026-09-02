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

Links (hard links) the tracks into the directory `to_upload`, with file
names cleaned up to exclude weird characters.

Links (hard links) the tracks into the directory
`to_chorus_connection`, with file names that include the tags that CC
wants, such as "(Bass)".

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
from collections.abc import Generator
from pathlib import Path


USAGE = """
Usage: organize.py

Reads from music/..., writes to to_upload/... and data/songs.json.
"""

MUSIC_FOLDER = "music"
TO_UPLOAD_FOLDER = "to_upload"
TO_CHORUS_CONNECTION_FOLDER = "to_chorus_connection"


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


TOP_PATTERN = re.compile("^([^-]*) - ([^-]*) - ([^-]*).mp3$")
PART_PATTERN = re.compile("^(alto|bass|tenor|soprano|descant|solo) (1 |2 |3 |solo |)(muted|predominant)$")


def parts_from_part_info(part_info: str) -> Generator[str, None, None]:
    if part_info == "Balanced Voices":
        yield "balancedvoices"
    elif part_info == "Accompaniment Track":
        pass
    else:
        m2 = PART_PATTERN.match(part_info.lower())
        if not m2:
            raise ValueError(f"Do not understand part info: {part_info!r}")
        part, high_low, volume = m2.groups()
        if volume == "muted" or volume == "descant" or part == "solo":
            pass
        elif volume == "predominant":
            if high_low == "1 ":
                yield part + "1"
            elif high_low == "2 ":
                yield part + "2"
            elif high_low == "":
                yield part + "1"
                yield part + "2"
            elif high_low == "solo ":
                pass
            else:
                raise ValueError(f"Do not understand part info (high_low): {part_info!r}")
        else:
            raise ValueError(f"Do not understand part info (volume): {part_info!r}")


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

     
class SongInfo:
    def __init__(self, original_file: Path):
        m1 = TOP_PATTERN.match(original_file.name)
        if not m1:
            raise ValueError(f"File name does not match top pattern: {original_file.name}")

        self.original_file = original_file
        self.original_name = original_file.name
        self.clean_name = clean_file_name(original_file.name)
        self.song_name = make_pretty_name(m1.group(1))
        self.part_info = m1.group(2)
        self.parts = sorted(parts_from_part_info(m1.group(2)))


def get_songs(all_files_folder):
    """Yields SongInfo objects for each file in the folder
    """
    for file in all_files_folder.iterdir():
        yield SongInfo(file)


def recursive_delete(p: Path):
    if p.is_dir():
        for sub in p.iterdir():
            recursive_delete(sub)
        p.rmdir()
    elif p.is_file():
        p.unlink()
    else:
        raise ValueError(f"not a file or directory: {p}")


def chorus_connection_part(part: str) -> str:
    """Convert 1/2-splits to plain parts.

    >>> chorus_connection_part("bass2")
    'Bass'
    >>> chorus_connection_part("balancedvoices")
    'ALL'
    """
    if part == "balancedvoices":
        return "ALL"
    else:
        assert part[-1] in ["1", "2"]
        return part[0].upper() + part[1:-1]


def main():
    if len(sys.argv) != 1:
        usage()
        
    music_folder = Path(MUSIC_FOLDER)
    all_files_folder = music_folder.joinpath("AllFiles")
    to_upload_folder = Path(TO_UPLOAD_FOLDER)
    to_chorus_connection_folder = Path(TO_CHORUS_CONNECTION_FOLDER)
    
    if not all_files_folder.is_dir():
        print(f"'{all_files_folder}' is not a directory", file=sys.stderr())
        sys.exit(1)

    if to_upload_folder.exists():
        recursive_delete(to_upload_folder)
    to_upload_folder.mkdir()

    if to_chorus_connection_folder.exists():
        recursive_delete(to_chorus_connection_folder)
    to_chorus_connection_folder.mkdir()

    # Process all songs
    song_to_parts = defaultdict(dict)
    for song in get_songs(all_files_folder):
        # Build song data
        for part in song.parts:
            song_to_parts[song.song_name][part] = song.clean_name

        # Link file to upload
        if 0 < len(song.parts):
            new_link = to_upload_folder.joinpath(song.clean_name)
            assert not new_link.exists()
            new_link.hardlink_to(song.original_file)
            print(f"linked: {new_link}")

        # Link file for chorus connection
        cc_parts = {chorus_connection_part(p) for p in song.parts}
        for cc_part in cc_parts:
            cc_name = f"{song.song_name}/{song.song_name} - {song.part_info}"
            if cc_part != "ALL":
                cc_name += f" ({cc_part})"
            cc_link = to_chorus_connection_folder.joinpath(cc_name)
            cc_link.parent.mkdir(parents=True, exist_ok=True)
            cc_link.hardlink_to(song.original_file)
            print(f"linked: {cc_link}")

    with open("data/songs.json", "w") as f:
        print(json.dumps(song_to_parts, sort_keys=True, indent=2), file=f)
    print("wrote data/songs.json")


if __name__ == "__main__":
    main()

