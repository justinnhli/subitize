#!/bin/bash

SCHEMA_SQL=subitize/data/schema.sql
DATA_SQL=subitize/data/data.sql
COUNTS_DB=subitize/data/counts.db
LAST_UPDATE=subitize/data/last-update
source ~/.venv/subitize/bin/activate && \
    cd ~/git/subitize/ && \
    rm -f "$COUNTS_DB" && \
    scripts/update-offerings.py && \
    scripts/dump.sh && \
    git add "$SCHEMA_SQL" "$DATA_SQL" "$LAST_UPDATE" && \
    git commit -m 'update DB' && \
    git push
