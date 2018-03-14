#!/bin/sh

if [ ! -e data/counts.db ]; then
	exit
fi
sqlite3 data/counts.db .schema > data/schema.sql
sqlite3 data/counts.db .dump > data/data.sql
case "$(uname)" in
"Linux")
	sed -i '1s/foreign_keys=OFF/foreign_keys=ON/' data/data.sql;;
"Darwin")
	sed -i '' '1s/foreign_keys=OFF/foreign_keys=ON/' data/data.sql;;
esac
rm -f data/counts.db
sqlite3 data/counts.db '.read data/data.sql'
if git status | grep modified >/dev/null; then
	date '+%Y-%m-%d %H:%M:%S %Z' > data/last-update
fi
