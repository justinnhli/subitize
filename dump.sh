#!/bin/sh

sqlite3 counts.db .schema > schema.sql
sqlite3 counts.db .dump > data.sql
