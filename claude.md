# MCAA Player Project

This is a static website used to play the practice recordings
for Maui Choral Arts.  Typical users will be on a phone or tablet,
but some may be on a computer.

The site is easy to use.  It is structured as a menu tree.

The first page asks you to pick your voice part.  The choices are:

 - Soprano 1
 - Soprano 2
 - Alto 1
 - Alto 2
 - Tenor 1
 - Tenor 2
 - Bass 1
 - Bass 2
 
Once you've picked your voice part, it takes you to the second page,
which lets you pick one of the songs.  The songs are:

 - Home
 - It's a Republic
 - Sure On This Shining Night
 - The Road Home
 - There's Gonna Be A Homecomin'
 
When you select a song, it takes you to a playback page for that song,
with your voice part dominant.  The page shows your voice part, the
title of the song, and has playback controls to pause and play.

# Project Structure

The folder `site` contains the static site, with the CSS and HTML files.
The folder `music` contains the MP3 files for the recordings to play.

The CSS is structured to use a minimal number of classes to style
the pages, with those classes reused on many elements to produce
a consistent style.  The overall look is simple and clear.

Under `music`, there is a folder for each song containing many different
versions of the song.  The naming convention for the files is:

 - <title>-<part><version>.mp3
 - <title>-Bal.mp3
 
The part is an abbreviated version of the voice part, one of: Sop1, Sop2, Alt1, etc.
If the high and low sections of one part are the same, the number may be left out.

The version is one of:

 - Dom - "dominant" - that part is dominant and is louder than the other parts
 - Mute - "mute" - that part is omitted
 
The "Bal" file has all parts at equal volumes.

