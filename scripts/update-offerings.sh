#!/bin/bash

counts_db=subitize/data/counts.db

source "$HOME/.bashrc" && \
    source "$HOME/.dot_secrets/bashrc" && \
    source $PYTHON_VENV_HOME/subitize/bin/activate && \
    cd ~/git/subitize/ && \
    rm -f "$counts_db" && \
    ./scripts/update-offerings.py && \
    ./scripts/dump.sh && \
    exit 0

exit 1
