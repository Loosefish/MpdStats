#!/bin/bash

stats_db=$1
sql="sqlite3 -header -column"


function top_artists() {
	${sql} -cmd '.width 40 8' ${stats_db} "
		SELECT album_artist, SUM(length) / 60 AS 'playtime'
			FROM plays
			GROUP BY album_artist
			ORDER BY playtime;
	"
}

function top_albums() {
	${sql} -cmd '.width 29 30 10 8' ${stats_db} "
		SELECT album_artist, album, album_date, SUM(length) / 60 AS 'playtime'
			FROM plays
			GROUP BY album_artist, album, album_date
			ORDER BY playtime;
	"
}

function top_songs() {
	${sql} -cmd '.width 39 30 9' ${stats_db} "
		SELECT artist, title, COUNT(*) AS 'playcount'
			FROM plays
			GROUP BY artist, title
			ORDER BY playcount;
	"
}

case $2 in
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

