#!/bin/sh

SCHEMA_SQL=subitize/data/schema.sql
DATA_SQL=subitize/data/data.sql
COUNTS_DB=subitize/data/counts.db
LAST_UPDATE=subitize/data/last-update
if [ ! -e "$COUNTS_DB" ]; then
	exit
fi
sqlite3 "$COUNTS_DB" .schema > "$SCHEMA_SQL"
sqlite3 "$COUNTS_DB" .dump > "$DATA_SQL"
case "$(uname)" in
"Linux")
	sed -i '1s/foreign_keys=OFF/foreign_keys=ON/' "$DATA_SQL";;
"Darwin")
	sed -i '' '1s/foreign_keys=OFF/foreign_keys=ON/' "$DATA_SQL";;
esac
rm -f "$COUNTS_DB"
sqlite3 "$COUNTS_DB" '.read data/data.sql'
if git status | grep modified >/dev/null; then
	date '+%Y-%m-%d %H:%M:%S %Z' > "$LAST_UPDATE"
fi
