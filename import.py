from stats_db import StatsDB

import csv

db_path = '/home/henry/.config/MusicStats/stats.db'
import_file = '/home/henry/.config/MusicStats/dump'


db = StatsDB(db_path)
with open(import_file, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter='|')
    for row in reader:
        db.register_play(row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[0])
