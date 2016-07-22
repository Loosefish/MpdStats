#!/bin/bash

stats_db="/home/henry/.config/MusicStats/stats.db"
sql="sqlite3 -header -column"


function top_artists() {
	${sql} -cmd '.width 40 8' ${stats_db} "
		SELECT album_artist, SUM(length) / 60 AS 'playtime'
			FROM plays JOIN songs ON plays.song = songs.id
			GROUP BY album_artist
			ORDER BY playtime;
	"
}

function top_albums() {
	${sql} -cmd '.width 29 30 10 8' ${stats_db} "
		SELECT album_artist, album, date, SUM(length) / 60 AS 'playtime'
			FROM plays JOIN songs ON plays.song = songs.id
			GROUP BY album_artist, album, date
			ORDER BY playtime;
	"
}

function top_songs() {
	${sql} -cmd '.width 39 30 9' ${stats_db} "
		SELECT artist, title, COUNT(*) AS 'playcount'
			FROM plays JOIN songs ON plays.song = songs.id
			GROUP BY artist, title
			ORDER BY playcount;
	"
}

case $1 in
	ar* )
		top_artists
		;;

	al* )
		top_albums
		;;

	s* )
		top_songs
		;;
esac

