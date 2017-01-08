# MpdStats #
A small python program which monitors mpd and records played songs in a sqlite database.

## Usage ##
```
usage: mpd_stats.py [-h] [-p PROGRESS] [-v] socket db_file

Keeps a database of songs played with mpd.

positional arguments:
  socket                mpd socket
  db_file               database location

optional arguments:
  -h, --help            show this help message and exit
  -p PROGRESS, --progress PROGRESS
                        minimal progress to register as a complete song
  -v, --verbose
```
