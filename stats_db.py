#!/usr/bin/env python
# encoding: utf-8

import sqlite3
from time import time


class StatsDB(object):
    def __init__(self, db_path):
        self.db_path = db_path

        c = sqlite3.connect(self.db_path)
        c.execute(
            '''CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY,
                artist TEXT,
                title TEXT,
                album_artist TEXT,
                album TEXT,
                date TEXT,
                track TEXT,
                length INTEGER,
                CONSTRAINT song UNIQUE (
                    artist,
                    title,
                    album_artist,
                    date,
                    track,
                    length
                ))'''
        )

        c.execute(
            '''CREATE TABLE IF NOT EXISTS plays (
                time INTEGER PRIMARY KEY,
                song INTEGER)'''
        )
        c.commit()
        c.close()

    def register_play(self, artist, title, album_artist, album, date, track, length, playtime=None):
        c = sqlite3.connect(self.db_path)
        c.execute(
            '''INSERT OR IGNORE INTO songs (
                artist,
                title,
                album_artist,
                album,
                date,
                track,
                length
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (artist, title, album_artist, album, date, track, length)
        )
        c.commit()

        song_id = c.execute(
            '''SELECT id
            FROM songs
            WHERE
                artist = ? AND
                title = ? AND
                album_artist = ? AND
                album = ? AND
                date = ? AND
                track = ? AND
                length = ?''',
            (artist, title, album_artist, album, date, track, length)
        ).fetchone()[0]

        if playtime:
            c.execute('''INSERT INTO plays VALUES (?, ?)''', (playtime, song_id))
        else:
            c.execute('''INSERT INTO plays VALUES (?, ?)''', (int(time()), song_id))
        c.commit()

        c.close()
