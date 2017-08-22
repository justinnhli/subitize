#!/bin/sh

sqlite3 counts.db .schema > schema.sql
sqlite3 counts.db .dump > data.sql
sed -i '' '1s/foreign_keys=OFF/foreign_keys=ON/' data.sql
rm -f counts.db
sqlite3 counts.db '.read data.sql'
