from time import time, sleep

from mpd import MPD
from stats_db import StatsDB


class MusicStats(object):
    def __init__(self, socket, db_path):
        self.mpd = MPD(socket)
        self.db = StatsDB(db_path)

    def wait(self, events):
        self.mpd._query('idle {}'.format(events))

    @staticmethod
    def retry(f):
        holdoff = 1
        while True:
            try:
                return f()
            except ConnectionRefusedError:
                print("Couldn't reach MPD. Retrying in {}s.".format(holdoff))
                sleep(holdoff)
                holdoff = min(holdoff * 2, 32)

    def played(self, song, progress):
        print("Registering play: {} - {}".format(song['Artist'], song['Title']))
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
        status = self.retry(self.mpd.get_status)
        if status['state'] == 'play':
            f = self.is_playing(status, self.retry(self.mpd.get_currentsong))
        elif status['state'] == 'pause':
            f = self.is_paused(status)
        elif status['state'] == 'stop':
            f = self.is_stopped()

        while True:
            f = f()

    def is_playing(self, status, song):
        checkpoint = time()

        self.wait('player')
        newstatus = self.retry(self.mpd.get_status)
        if newstatus['state'] == 'stop':
            progress = (status['time'] + time() - checkpoint) / status['duration']
            self.played(song, progress)
            return self.is_stopped

        elif newstatus['state'] == 'play':
            newsong = self.retry(self.mpd.get_currentsong)
            if newsong['Id'] != song['Id']:
                progress = (status['time'] + time() - checkpoint) / status['duration']
                self.played(song, progress)
            return lambda: self.is_playing(newstatus, newsong)

        else:
            return lambda: self.is_paused(newstatus)

    def is_paused(self, status):
        song = self.retry(self.mpd.get_currentsong)

        self.wait('player')
        newstatus = self.retry(self.mpd.get_status)

        if newstatus['state'] == 'stop':
            progress = status['time'] / status['duration']
            self.played(song, progress)
            return self.is_stopped

        elif newstatus['state'] == 'play':
            newsong = self.retry(self.mpd.get_currentsong)
            if newsong['Id'] != song['Id']:
                progress = status['time'] / status['duration']
                self.played(song, progress)
            return lambda: self.is_playing(newstatus, newsong)

        else:
            return lambda: self.is_paused(newstatus)

    def is_stopped(self):
        self.wait('player')
        status = self.retry(self.mpd.get_status)

        if status['state'] == 'play':
            return lambda: self.is_playing(status, self.retry(self.mpd.get_currentsong))
        elif status['state'] == 'pause':
            return lambda: self.is_paused(status)
        else:
            return self.is_stopped


if __name__ == '__main__':
    STATS = MusicStats('/home/henry/.config/mpd/socket', '/home/henry/.config/MusicStats/stats.db')
    try:
        STATS.monitor()
    except KeyboardInterrupt:
        pass
