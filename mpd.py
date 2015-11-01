import socket


class MPD(object):
    def __init__(self, socket):
        self.socket = socket

    def _query(self, text):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # s.settimeout(5)
        s.connect(self.socket)
        data = s.recv(32)
        s.sendall(bytes(text + '\n', 'utf8'))
        response = b""
        while True:
            data = s.recv(4096)
            response = response + data
            if data[-4:] == b'\nOK\n' or data == b'OK\n':
                break
        s.close()
        return str(response, 'utf8').splitlines()[:-1]

    def _get_dicts(self, query):
        response = self._query(query)
        new_token = response[0].split(': ', 1)[0]
        dicts = []
        for r in response:
            tag, value = r.split(': ', 1)
            if tag == new_token:
                d = dict([(tag, value)])
                dicts.append(d)
            else:
                d[tag] = value
        return dicts

    def get_song(self, filename):
        query = 'find file "{}"'.format(filename)
        song = self._get_dicts(query)[0]
        song['Time'] = int(song['Time'])

    def get_songs(self, album_artist, date, album):
        query = 'find AlbumArtist "{}" Date "{}" Album "{}"'.format(album_artist, date, album)
        songs = self._get_dicts(query)
        for s in songs:
            s['Time'] = int(s['Time'])
        return songs

    def get_album_artists(self):
        return self._get_dicts('list AlbumArtist')

    def get_albums(self, album_artist=None):
        if album_artist:
            query = 'list Album AlbumArtist "{}" group AlbumArtist group Date'.format(album_artist)
        else:
            query = 'list AlbumArtist group Album group Date'
        return self._get_dicts(query)

    def search_songs(self, tag, query):
        return self._get_dicts('search {} "{}"'.format(tag, query))

    def get_status(self):
        converters = {
            'bitrate': int,
            'consume': lambda x: bool(int(x)),
            'elapsed': float,
            'mixrampdb': float,
            'nextsong': int,
            'nextsongid': int,
            'playlist': int,
            'playlistlength': int,
            'random': lambda x: bool(int(x)),
            'repeat': lambda x: bool(int(x)),
            'single': lambda x: bool(int(x)),
            'song': int,
            'songid': int,
            'volume': int
        }

        status = self._get_dicts('status')[0]
        for k, v in status.items():
            if k in converters:
                status[k] = converters[k](v)

        if 'time' in status:
            status['time'], status['duration'] = (int(x) for x in status['time'].split(':'))

        return status

    def get_currentsong(self):
        try:
            return self._get_dicts('currentsong')[0]
        except IndexError:
            return None

    def get_playlist(self):
        return self._get_dicts('playlistinfo')

    def playlist_clear(self):
        self._query('clear')

    def playlist_add(self, song_file):
        self._query('add "{}"'.format(song_file))

    def playlist_add_album(self, album_artist, date, album):
        self._query('findadd AlbumArtist "{}" Date "{}" Album "{}"'
                    .format(album_artist, date, album))

    def playlist_remove(self, index):
        self._query('delete {}'.format(index))

    def playlist_move(self, index, to):
        self._query('move {} {}'.format(index, to))

    def play(self, index=0):
        self._query('play {}'.format(index))

    def pause_toggle(self):
        if self.get_status()['state'] == 'play':
            self._query('pause 1')
        else:
            self._query('pause 0')

    def stop(self):
        self._query('stop')

    def next(self):
        self._query('next')

    def previous(self):
        self._query('previous')

    def repeat_toggle(self):
        if self.get_status()['repeat']:
            self._query('repeat 0')
        else:
            self._query('repeat 1')

    def random_toggle(self):
        if self.get_status()['random']:
            self._query('random 0')
        else:
            self._query('random 1')

    def single_toggle(self):
        if self.get_status()['single']:
            self._query('single 0')
        else:
            self._query('single 1')
