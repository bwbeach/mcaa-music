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


def read_json(file_path):
    with open(file_path, "r") as f:
        return json.loads(f.read())


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

    # Extract the names of the songs
    song_names = sorted(song_data.keys())

    # Definitions of variables used by templates
    template_data = dict(
        is_local=is_local,
        song_names=song_names,
    )


if __name__ == "__main__":
    main()
