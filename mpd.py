import socket


class MPD(object):
    def __init__(self, addr):
        self.addr = addr

    def _query(self, text):
        conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # conn.settimeout(5)
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

    def get_song(self, filename):
        query = 'find file "{}"'.format(filename)
        song = self._get_dicts(query)[0]
        song['Time'] = int(song['Time'])

    def get_songs(self, album_artist, date, album):
        query = 'find AlbumArtist "{}" Date "{}" Album "{}"'.format(album_artist, date, album)
        songs = self._get_dicts(query)
        for song in songs:
            song['Time'] = int(song['Time'])
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
        for key, val in status.items():
            if key in converters:
                status[key] = converters[key](val)

        if 'time' in status:
            status['time'], status['duration'] = (int(x) for x in status['time'].split(':'))

        return status

    def get_currentsong(self):
        try:
            return self._get_dicts('currentsong')[0]
        except IndexError:
            return None
