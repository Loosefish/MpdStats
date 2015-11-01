from mpd import MPD
from stats_db import StatsDB
from time import time


class MusicStats(object):
    def __init__(self, socket, db_path):
        self.mpd = MPD(socket)
        self.db = StatsDB(db_path)

    def wait(self, events):
        self.mpd._query('idle {}'.format(events))

    def played(self, song, progress):
        if progress > 0.6:
            self.db.register_play(
                song['Artist'],
                song['Title'],
                song['AlbumArtist'],
                song['Album'],
                song['Date'],
                song['Track'],
                int(song['Time'])
            )

    def monitor(self):
        status = self.mpd.get_status()
        if status['state'] == 'play':
            f = self.is_playing(status, self.mpd.get_currentsong())
        elif status['state'] == 'pause':
            f = self.is_paused(status)
        elif status['state'] == 'stop':
            f = self.is_stopped()

        while True:
            f = f()

    def is_playing(self, status, song):
        checkpoint = time()

        self.wait('player')
        newstatus = self.mpd.get_status()
        if newstatus['state'] == 'stop':
            progress = (status['time'] + time() - checkpoint) / status['duration']
            self.played(song, progress)
            return (lambda: self.is_stopped())

        elif newstatus['state'] == 'play':
            newsong = self.mpd.get_currentsong()
            if newsong['Id'] != song['Id']:
                progress = (status['time'] + time() - checkpoint) / status['duration']
                self.played(song, progress)
            return (lambda: self.is_playing(newstatus, newsong))

        else:
            return (lambda: self.is_paused(newstatus))

    def is_paused(self, status):
        song = self.mpd.get_currentsong()

        self.wait('player')
        newstatus = self.mpd.get_status()

        if newstatus['state'] == 'stop':
            progress = status['time'] / status['duration']
            self.played(song, progress)
            return (lambda: self.is_stopped())

        elif newstatus['state'] == 'play':
            newsong = self.mpd.get_currentsong()
            if newsong['Id'] != song['Id']:
                progress = status['time'] / status['duration']
                self.played(song, progress)
            return (lambda: self.is_playing(newstatus, newsong))

        else:
            return (lambda: self.is_paused(newstatus))

    def is_stopped(self):
        self.wait('player')
        status = self.mpd.get_status()

        if status['state'] == 'play':
            return (lambda: self.is_playing(status, self.mpd.get_currentsong()))
        elif status['state'] == 'pause':
            return (lambda: self.is_paused(status))
        else:
            return (lambda: self.is_stopped())


if __name__ == '__main__':
    ms = MusicStats('/home/henry/.config/mpd/socket', '/home/henry/.config/MusicStats/stats.db')
    try:
        ms.monitor()
    except KeyboardInterrupt:
        pass
