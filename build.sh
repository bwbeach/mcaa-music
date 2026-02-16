#!/bin/bash

# Fail if any subcommand fails.
set -e

# Prepare the distribution folder where we'll put the website.
rm -rf dist
mkdir dist

# Copy the static files
cp static/* dist

# Install `uv` if it doesn't exist.  This is needed in the github action.
if uv --version; then
    echo "uv already available"
else
    pip install uv
fi
    
# Run tests
uv run --python 3.14 --with jinja2 python -m doctest -v tools/*.py 

# Generate the generated files
tools/generate.py $* data/songs.json templates dist
