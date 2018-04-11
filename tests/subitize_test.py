#!/usr/bin/env python3

# pylint: disable = missing-docstring, wrong-import-position

import sys
from os.path import dirname, realpath, join as join_path

sys.path.append(join_path(dirname(realpath(__file__)), '..', '..'))

from subitize import create_session, create_query
from subitize import filter_by_semester, filter_by_department, filter_by_number, filter_by_instructor
from subitize import filter_by_units, filter_by_core, filter_by_meeting

def test_semester_query():
    session = create_session()
    query = create_query(session)
    query = filter_by_semester(session, query, 201701)
    assert all(offering.semester_id == 201701 for offering in query)
    assert query.count() == 816


def test_department_query():
    session = create_session()
    query = create_query(session)
    query = filter_by_semester(session, query, 201701)
    query = filter_by_department(session, query, 'COGS')
    assert all(offering.course.department.code == 'COGS' for offering in query)
    assert query.count() == 15


def test_number_query():
    session = create_session()
    query = create_query(session)
    query = filter_by_semester(session, query, 201701)
    query = filter_by_department(session, query, 'COGS')
    query = filter_by_number(session, query, minimum=200, maximum=300)
    assert all(200 <= offering.course.number_int <= 300 for offering in query)
    assert query.count() == 8


def test_unit_query():
    session = create_session()
    query = create_query(session)
    query = filter_by_semester(session, query, 201701)
    query = filter_by_department(session, query, 'COGS')
    query = filter_by_units(session, query, 2)
    assert all(offering.units == 2 for offering in query)
    assert query.count() == 2


def test_instructor_query():
    session = create_session()
    query = create_query(session)
    query = filter_by_semester(session, query, 201701)
    query = filter_by_instructor(session, query, 'Justin Li')
    assert query.count() == 4


def test_core_query():
    session = create_session()
    query = create_query(session)
    query = filter_by_semester(session, query, 201701)
    query = filter_by_core(session, query, 'CPFA')
    query = filter_by_core(session, query, 'CPGC')
    query = filter_by_core(session, query, 'CPPE')
    assert query.count() == 1


def test_meeting_query_normal():
    session = create_session()
    query = create_query(session)
    query = filter_by_semester(session, query, 201701)
    query = filter_by_department(session, query, 'COGS')
    query = filter_by_meeting(session, query, days='T')
    assert query.count() == 6


def test_meeting_query_tbd():
    session = create_session()
    query = create_query(session)
    query = filter_by_semester(session, query, 201701)
    query = filter_by_department(session, query, 'COGS')
    query = filter_by_meeting(session, query, days='MTWRFU')
    assert query.count() == 2
