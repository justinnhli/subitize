#!/bin/sh

schema_sql=subitize/data/schema.sql
data_sql=subitize/data/data.sql
counts_db=subitize/data/counts.db
last_update=subitize/data/last-update

if [ ! -e "$counts_db" ]; then
	exit
fi
sqlite3 "$counts_db" .schema > "$schema_sql"
sqlite3 "$counts_db" .dump > "$data_sql"
case "$(uname)" in
"Linux")
	sed -i '1s/foreign_keys=OFF/foreign_keys=ON/' "$data_sql";;
"Darwin")
	sed -i '' '1s/foreign_keys=OFF/foreign_keys=ON/' "$data_sql";;
esac
rm -f "$counts_db"
sqlite3 "$counts_db" ".read $data_sql"
if git status | grep modified >/dev/null; then
	date '+%Y-%m-%d %H:%M:%S %Z' > "$last_update"
fi
