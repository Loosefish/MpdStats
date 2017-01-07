#!/usr/bin/env python
from time import time
import argparse
import logging
import socket
import sqlite3
import sys


class Mpd():
    def __init__(self, addr):
        self.addr = addr

    def _query(self, text):
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        conn.connect(self.addr)
        data = conn.recv(32)
        conn.sendall(bytes(text + '\n', 'utf8'))
        response = b""
        while True:
            data = conn.recv(4096)
            response = response + data
            if data[-4:] == b'\nOK\n' or data == b'OK\n':
                break
        conn.close()
        return str(response, 'utf8').splitlines()[:-1]

    def _get_dicts(self, query):
        response = self._query(query)
        new_token = response[0].split(': ', 1)[0]
        dicts = []
        for res in response:
            tag, value = res.split(': ', 1)
            if tag == new_token:
                this = dict([(tag, value)])
                dicts.append(this)
            else:
                this[tag] = value
        return dicts

    def get_status(self):
        status = self._get_dicts('status')[0]
        if 'time' in status:
            status['time'], status['duration'] = tuple(map(int, status["time"].split(":")))
        return status

    def get_currentsong(self):
        try:
            return self._get_dicts('currentsong')[0]
        except IndexError:
            return None

    def wait(self, events):
        self._query('idle {}'.format(events))


class Stats():
    def __init__(self, db_path):
        self.db_path = db_path

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''CREATE TABLE IF NOT EXISTS plays (
                    time INTEGER PRIMARY KEY,
                    artist TEXT,
                    title TEXT,
                    album TEXT,
                    album_artist TEXT,
                    album_date TEXT,
                    track TEXT,
                    length INTEGER
                    )'''
            )

    def register_play(self, playtime, artist, title, album, album_artist, album_date, track, length):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                '''INSERT INTO plays (
                    time,
                    artist,
                    title,
                    album,
                    album_artist,
                    album_date,
                    track,
                    length
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (playtime, artist, title, album, album_artist, album_date, track, length)
            )


class Monitor():
    def __init__(self, socket, db_path, min_prog):
        self.mpd = Mpd(socket)
        self.stats = Stats(db_path)
        self.min_prog = min_prog
        self.log = logging.getLogger(__name__)

    @staticmethod
    def retry(f):
        pause = 1
        while True:
            try:
                return f()
            except ConnectionRefusedError:
                self.log.error("connection refused - retrying in %ss", pause)
                sleep(pause)
                pause = min(holdoff * 2, 32)

    def played(self, song, progress):
        if progress > self.min_prog:
            self.log.info("registering play: %s - %s", song["Artist"], song["Title"])
            self.stats.register_play(
                int(time()),
                song["Artist"],
                song["Title"],
                song["Album"],
                song["AlbumArtist"],
                song["Date"],
                song["Track"],
                int(song["Time"])
            )

    def run(self):
        status = self.retry(self.mpd.get_status)
        if status["state"] == "play":
            f = self.playing(status, self.retry(self.mpd.get_currentsong))
        elif status["state"] == "pause":
            f = self.paused(status)
        elif status["state"] == "stop":
            f = self.stopped()

        while True:
            f = f()

    def playing(self, status, song):
        self.log.debug("new state [playing] ('%s')", song["file"])

        checkpoint = time()
        self.mpd.wait("player")
        newstatus = self.retry(self.mpd.get_status)
        if newstatus["state"] == "stop":
            progress = (status["time"] + time() - checkpoint) / status["duration"]
            self.played(song, progress)
            return self.stopped

        elif newstatus["state"] == "play":
            newsong = self.retry(self.mpd.get_currentsong)
            if newsong["Id"] != song["Id"]:
                progress = (status["time"] + time() - checkpoint) / status["duration"]
                self.played(song, progress)
            return lambda: self.playing(newstatus, newsong)

        else:
            return lambda: self.paused(newstatus)

    def paused(self, status):
        self.log.debug("new state [paused]")

        song = self.retry(self.mpd.get_currentsong)
        self.mpd.wait("player")
        newstatus = self.retry(self.mpd.get_status)

        if newstatus["state"] == "stop":
            progress = status["time"] / status["duration"]
            self.played(song, progress)
            return self.stopped

        elif newstatus["state"] == "play":
            newsong = self.retry(self.mpd.get_currentsong)
            if newsong["Id"] != song["Id"]:
                progress = status["time"] / status["duration"]
                self.played(song, progress)
            return lambda: self.playing(newstatus, newsong)

        else:
            return lambda: self.paused(newstatus)

    def stopped(self):
        self.log.debug("new state [stopped]")

        self.mpd.wait("player")
        status = self.retry(self.mpd.get_status)
        if status["state"] == "play":
            return lambda: self.playing(status, self.retry(self.mpd.get_currentsong))
        elif status["state"] == "pause":
            return lambda: self.paused(status)
        else:
            return self.stopped


def main():
    parser = argparse.ArgumentParser(description='Keeps a database of songs played with mpd.')
    parser.add_argument("socket", help="mpd socket")
    parser.add_argument("db_file", help="database location")
    parser.add_argument("-p", "--progress", help="minimal progress to register as a complete song", type=float, default=0.6)
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    assert(args.progress >= 0 and args.progress <= 1.0)
        
    stats = Monitor(args.socket, args.db_file, args.progress)
    try:
        stats.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
