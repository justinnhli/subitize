#!/usr/bin/env python3

# pylint: disable = missing-docstring, wrong-import-position

import sys
from os.path import dirname, realpath, join as join_path
from pathlib import Path

from sqlalchemy.sql.expression import func

sys.path.append(str(Path(__file__).resolve().parent.parent))

from subitize import create_session, create_select
from subitize import filter_by_semester, filter_by_department, filter_by_number, filter_by_instructor
from subitize import filter_by_units, filter_by_core, filter_by_meeting

def test_semester_query():
    query = create_select()
    query = filter_by_semester(query, 201701)
    with create_session() as session:
        assert all(offering.semester_id == 201701 for offering in session.scalars(query))
        assert len(list(session.scalars(query))) == 816


def test_department_query():
    query = create_select()
    query = filter_by_semester(query, 201701)
    query = filter_by_department(query, 'COGS')
    with create_session() as session:
        assert all(offering.course.department.code == 'COGS' for offering in session.scalars(query))
        assert len(list(session.scalars(query))) == 15


def test_number_query():
    query = create_select()
    query = filter_by_semester(query, 201701)
    query = filter_by_department(query, 'COGS')
    query = filter_by_number(query, minimum=200, maximum=300)
    with create_session() as session:
        assert all(200 <= offering.course.number_int <= 300 for offering in session.scalars(query))
        assert len(list(session.scalars(query))) == 8


def test_unit_query():
    query = create_select()
    query = filter_by_semester(query, 201701)
    query = filter_by_department(query, 'COGS')
    query = filter_by_units(query, 2)
    with create_session() as session:
        assert all(offering.units == 2 for offering in session.scalars(query))
        assert len(list(session.scalars(query))) == 2


def test_instructor_query():
    query = create_select()
    query = filter_by_semester(query, 201701)
    query = filter_by_instructor(query, 'Justin Li')
    with create_session() as session:
        assert len(list(session.scalars(query))) == 4


def test_core_query():
    query = create_select()
    query = filter_by_semester(query, 201701)
    query = filter_by_core(query, 'CPFA')
    query = filter_by_core(query, 'CPGC')
    query = filter_by_core(query, 'CPPE')
    with create_session() as session:
        assert len(list(session.scalars(query))) == 1


def test_meeting_query_normal():
    query = create_select()
    query = filter_by_semester(query, 201701)
    query = filter_by_department(query, 'COGS')
    query = filter_by_meeting(query, days='T')
    with create_session() as session:
        assert len(list(session.scalars(query))) == 6


def test_meeting_query_tbd():
    query = create_select()
    query = filter_by_semester(query, 201701)
    query = filter_by_department(query, 'COGS')
    query = filter_by_meeting(query, days='MTWRFU')
    with create_session() as session:
        assert len(list(session.scalars(query))) == 2


if __name__ == '__main__':
    test_semester_query()
    test_department_query()
    test_number_query()
    test_unit_query()
    test_instructor_query()
    test_core_query()
    test_meeting_query_normal()
    test_meeting_query_tbd()
