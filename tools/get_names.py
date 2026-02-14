#!/usr/bin/env -S uv run --python 3.14

"""
The `music` folder named on the command line is expected to hold one sub-folder
for each song.  Each of those sub-folders contains all of the variations of the
song.

This script validates that structure, then writes a json map from sub-folder name
to the names of all variation files in it.
"""

import json
import os.path
import sys


USAGE = """
Usage: get_names.py <musicFolder>
"""

def usage():
    print(USAGE, file=sys.stdout)
    sys.exit(1)


def get_song_folders(music_folder):
    """Lists all of the song folders under the main music folder.

    Yields pairs: (path_to_song_folder, song_folder_name)
    """
    for song_name in os.listdir(music_folder):
        song_folder = os.path.join(music_folder, song_name)
        if not os.path.isdir(song_folder):
            print(f"'{song_folder}' is not a directory", file = sys.stder())
            sys.exit(1)
        yield song_folder, song_name


def get_song_files(song_folder):
    """Lists the song files in one song folder.
    """
    for song_file in os.listdir(song_folder):
        song_path = os.path.join(song_folder, song_file)
        if not os.path.isfile(song_path):
            print(f"'{song_path} is not a '.mp3' file", song_path)
        yield song_file

        
def main():
    if len(sys.argv) != 2:
        usage()
        
    music_folder = sys.argv[1]
    if not os.path.isdir(music_folder):
        print(f"'{music_folder}' is not a directory", file=sys.stderr())
        sys.exit(1)

    result = dict(
        (song_name, list(get_song_files(song_folder)))
        for (song_folder, song_name) in get_song_folders(music_folder)
    )
    print(json.dumps(result, sort_keys=True, indent=2))
        
    
if __name__ == "__main__":
    main()
