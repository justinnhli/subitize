#!/bin/bash

counts_db=subitize/data/counts.db

. "$HOME/.bashrc" && \
    . "$PYTHON_VENV_HOME/subitize/bin/activate" && \
    cd "$HOME/git/subitize/" && \
    rm -f "$counts_db" && \
    ./scripts/update-offerings.py && \
    ./scripts/dump.sh && \
    exit 0

exit 1
