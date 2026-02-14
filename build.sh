#!/bin/bash

# Fail if any subcommand fails.
set -e

# Prepare the distribution folder where we'll put the website.
rm -rf dist
mkdir dist

# Copy the static files
cp static/* dist

# Generate the generated files
tools/generate.py data/songs.json templates dist



