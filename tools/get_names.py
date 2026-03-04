#!/usr/bin/env -S uv run --python 3.14

"""
The `music` folder named on the command line is expected to hold one sub-folder
for each song.  Each of those sub-folders contains all of the variations of the
song.

This script validates that structure, then writes a json map from sub-folder name
to the names of all variation files in it.
"""

import json
import sys

from pathlib import Path


USAGE = """
Usage: get_names.py <music>

Assumes that the music folder contains ByPiece/ and Pronunciation/
"""

def usage():
    print(USAGE, file=sys.stderr)
    sys.exit(1)


def get_song_folders(by_piece_folder):
    """Lists all of the song folders under the main music folder.

    Yields pairs: (path_to_song_folder, song_folder_name)
    """
    for song_folder in by_piece_folder.iterdir():
        song_name = song_folder.name
        if not song_folder.is_dir():
            print(f"'{song_folder}' is not a directory", file = sys.stderr())
            sys.exit(1)
        yield song_folder, song_name


def get_song_files(music_folder, song_folder):
    """Lists the song files in one song folder.
    """
    for song_file in song_folder.iterdir():
        if not song_file.is_file() or song_file.suffix != ".mp3":
            print(f"'{song_file} is not a '.mp3' file", file = sys.stderr())
            sys.exit(1)
        yield str(song_file.relative_to(music_folder))

        
def main():
    if len(sys.argv) != 2:
        usage()
        
    music_folder = Path(sys.argv[1])
    by_piece_folder = music_folder.joinpath("ByPiece")
    pronunciation_folder = music_folder.joinpath("Pronunciation")
    
    if not by_piece_folder.is_dir():
        print(f"'{by_piece_folder}' is not a directory", file=sys.stderr())
        sys.exit(1)

    if not pronunciation_folder.is_dir():
        print(f"'{pronunciation_folder}' is not a directory", file=sys.stderr())
        sys.exit(1)

    by_piece = dict(
        (song_name, list(get_song_files(music_folder, song_folder)))
        for (song_folder, song_name) in get_song_folders(by_piece_folder)
    )
    pronunciation = dict(
        ("Keoni - " + p.stem, [str(p.relative_to(music_folder))])
        for p in pronunciation_folder.iterdir()
    )

    result = {}
    result.update(by_piece)
    result.update(pronunciation)
    
    print(json.dumps(result, sort_keys=True, indent=2))
        
    
if __name__ == "__main__":
    main()
