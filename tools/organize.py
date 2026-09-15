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
PART_PATTERN = re.compile("^(alto|baritone|bass|tenor|soprano|descant|solo) (1 |2 |3 |sol[oi] |)(muted|predominant)$")


class PartInfo:
    """What part(s) does a recording apply to?

    Holds:
        part - one of: alto, bass, tenor, soprano, all
        high_low - one of: upper, lower, both
        solo - boolean

    >>> PartInfo("soprano", "upper", False).parts_for_web()
    ['soprano1']
    >>> PartInfo("soprano", "lower", False).parts_for_web()
    ['soprano2']
    >>> PartInfo("soprano", "both", False).parts_for_web()
    ['soprano1', 'soprano2']
    """

    def __init__(self, part: str, high_low: str, solo: str | None):
        if part == "descant":  # TODO - figure out a cleaner way to handle this
            part = "all"
            solo = "Descant"
        if part not in ["all", "alto", "bass", "tenor", "soprano"]:
            raise ValueError(f"unknown part: {part!r}")
        if high_low not in ["both", "upper", "lower"]:
            raise ValueError(f"unknown high_low: {high_low!r}")
        self._part = part
        self._high_low = high_low
        self._solo = solo

    @property
    def solo(self) -> bool:
        return self._solo is not None

    def parts_for_web(self) -> list[str]:
        if self._solo:
            return []
        elif self._part == "all":
            return ["balancedvoices"]
        else:
            match self._high_low:
                case "both": return [f"{self._part}1", f"{self._part}2"]
                case "upper": return [f"{self._part}1"]
                case "lower": return [f"{self._part}2"]
                case _: raise Exception(f"BUG: part not handled: {self._part!r}")

    def part_for_cc(self) -> str:
        if self._part == "all":
            return "ALL"
        else:
            return self._part.capitalize()
    

    def __repr__(self):
        return f"PartInfo({self._part!r}, {self._high_low!r}, {self._solo!r})"
        


def part_from_part_str(part_str: str) -> PartInfo | None:
    """Parse the string describing which part a recording is for.

    >>> part_from_part_str("Soprano 1 Muted")
    >>> part_from_part_str("Soprano 1 Predominant")
    PartInfo('soprano', 'upper', None)
    >>> part_from_part_str("Descant Predominant")
    PartInfo('all', 'both', 'Descant')
    >>> part_from_part_str("Bass soli Predominant")
    PartInfo('bass', 'both', 'bass soli')
    """
    # TODO - clean up
    if part_str == "Solo Predominant":  # TODO - clean up
        return PartInfo("all", "both", "Solo")
    elif part_str == "Balanced Voices":
        return PartInfo("all", "both", None)
    elif part_str == "Accompaniment Track":
        return None
    else:
        m2 = PART_PATTERN.match(part_str.lower())
        if not m2:
            raise ValueError(f"Do not understand part string: {part_str!r}")
        part, high_low, volume = m2.groups()
        if part == "baritone":
            part = "bass"
        if volume == "muted": 
            return None  # TODO: soli
        elif volume == "descant" or part == "solo":
            return PartInfo(part, "both", f"{part} {high_low.strip()}")
        elif volume == "predominant":
            if high_low == "1 ":
                return PartInfo(part, "upper", None)
            elif high_low == "2 ":
                return PartInfo(part, "lower", None)
            elif high_low == "":
                return PartInfo(part, "both", None)
            elif high_low == "solo " or high_low == "soli ":
                return PartInfo(part, "both", f"{part} {high_low.strip()}")
            else:
                raise ValueError(f"Do not understand part info (high_low): {part_str!r}")
        else:
            raise ValueError(f"Do not understand part info (volume): {part_str!r}")


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
        self.part = part_from_part_str(m1.group(2))

    @property
    def solo_name(self):
        """Name to use for the button in the solos section"""
        return f"{self.song_name} {self.part._solo}"


def get_songs(all_files_folder):
    """Yields SongInfo objects for each file in the folder that maps to a part we care about.
    """
    for file in all_files_folder.iterdir():
        song_info = SongInfo(file)
        if song_info.part is not None:
            yield song_info


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
    solo_to_file = {}
    for song in get_songs(all_files_folder):
        # Build song data
        if song.part.solo:
            solo_to_file[song.solo_name] = song.clean_name
        else:
            for part in song.part.parts_for_web():
                song_to_parts[song.song_name][part] = song.clean_name

        # Link file to upload
        new_link = to_upload_folder.joinpath(song.clean_name)
        assert not new_link.exists()
        new_link.hardlink_to(song.original_file)
        print(f"linked: {new_link}")
        
        # Link file for chorus connection
        cc_part = song.part.part_for_cc()
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

    with open("data/soli.json", "w") as f:
        print(json.dumps(solo_to_file, sort_keys=True, indent=2), file=f)
    print("wrote data/soli.json")


if __name__ == "__main__":
    main()

