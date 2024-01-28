#!/usr/bin/env python3

import sys
from pathlib import Path

ROOT_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIRECTORY))

from subitize import create_session, create_select, filter_by_semester


def main():
    session = create_session()
    statement = create_select()
    statement = filter_by_semester(statement, '202402')
    for offering in session.scalars(statement):
        print(offering)


if __name__ == '__main__':
    main()
