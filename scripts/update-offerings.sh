#!/bin/bash

counts_db=subitize/data/counts.db

source ~/.venv/subitize/bin/activate && \
    cd ~/git/subitize/ && \
    rm -f "$counts_db" && \
    ./scripts/update-offerings.py && \
    ./scripts/dump.sh && \
    exit 0

exit 1
