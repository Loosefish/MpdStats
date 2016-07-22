import csv

from stats_db import StatsDB


DB_PATH = '/home/henry/.config/MusicStats/stats.db'
IMPORT_FILE = '/home/henry/.config/MusicStats/dump'


db = StatsDB(DB_PATH)
with open(IMPORT_FILE, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter='|')
    for row in reader:
        db.register_play(row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[0])
