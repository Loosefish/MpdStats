#!/usr/bin/env python
# encoding: utf-8

import sqlite3
from time import time


class StatsDB(object):
    def __init__(self, db_path):
        self.db_path = db_path

        conn = sqlite3.connect(self.db_path)
        conn.execute(
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

        conn.execute(
            '''CREATE TABLE IF NOT EXISTS plays (
                time INTEGER PRIMARY KEY,
                song INTEGER)'''
        )

        conn.execute(
            '''CREATE VIEW IF NOT EXISTS plays_pretty AS
                SELECT datetime(time, "unixepoch"), artist, title,
                    album_artist, album, date, track, length
                FROM plays JOIN songs ON plays.song = songs.id'''
            )
        conn.commit()
        conn.close()

    def register_play(self, artist, title, album_artist, album, date, track, length, playtime=None):
        conn = sqlite3.connect(self.db_path)
        conn.execute(
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
        conn.commit()

        song_id = conn.execute(
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
            conn.execute('''INSERT INTO plays VALUES (?, ?)''', (playtime, song_id))
        else:
            conn.execute('''INSERT INTO plays VALUES (?, ?)''', (int(time()), song_id))
        conn.commit()

        conn.close()
