#!/usr/bin/env python3

from sqlalchemy.sql.expression import and_, or_, text, asc, desc

from models import Semester, TimeSlot, Meeting, Core, Department, Course, Person, Offering, OfferingMeeting, OfferingCore, OfferingInstructor

def filter_study_abroad(query):
    return query.filter(Department.code != 'OXAB', Department.code.notilike('AB%'))

def filter_by_search(query, terms=None):
    if terms is None:
        return query
    terms = terms.split()
    for term in terms:
        query = query.filter(or_(
            Offering.title.ilike('%{}%'.format(term)),
            Course.number == term,
            Department.code == term,
            Department.name.ilike('%{}%'.format(term)),
            Core.code == term,
            Core.name.ilike('%{}%'.format(term)),
            Person.system_name.ilike('%{}%'.format(term)),
            Person.first_name.ilike('%{}%'.format(term)),
            Person.last_name.ilike('%{}%'.format(term)),
            Person.nick_name.ilike('%{}%'.format(term)),
        ))
    return query

def filter_by_semester(query, semester=None):
    if semester is None:
        return query
    return query.filter(Semester.id == semester)

def filter_by_openness(query):
    return query.filter(and_(Offering.num_waitlisted == 0, text('num_enrolled < num_seats - num_reserved')))

def filter_by_instructor(query, instructor=None):
    if instructor is None:
        return query
    return query.filter(Person.system_name == instructor)

def filter_by_core(query, core=None):
    if core is None:
        return query
    return query.filter(Core.code == core)

def filter_by_units(query, units=None):
    if units is None:
        return query
    return query.filter(Offering.units == units)

def filter_by_department(query, department=None):
    if department is None:
        return query
    return query.filter(Department.id == department.id)

def filter_by_number(query, minimum=None, maximum=None):
    filters = []
    if minimum is not None:
        filters.append(Course.number_int >= minimum)
    if maximum is not None:
        filters.append(Course.number_int <= maximum)
    if filters:
        query = query.filter(*filters)
    return query

def filter_by_meeting(query, day=None, starts_after=None, ends_before=None):
    filters = []
    if day is not None:
        filters.append(or_(TimeSlot.weekdays == None, TimeSlot.weekdays.contains(day)))
    if starts_after is not None:
        filters.append(or_(TimeSlot.start == None, TimeSlot.start >= starts_after))
    if ends_before is not None:
        filters.append(or_(TimeSlot.end == None, TimeSlot.end <= ends_before))
    if filters:
        query = query.filter(*filters)
    return query

def sort_offerings(query, field=None):
    if field is None:
        query = query.order_by(
            desc(Semester.id),
            asc(Department.name),
            asc(Course.number_int),
            asc(Course.number),
            asc(Offering.section),
        )
    elif field == 'semester':
        query = query.order_by(
            asc(Semester.id),
        )
    elif field == 'course':
        query = query.order_by(
            asc(Department.code),
            asc(Course.number_int),
            asc(Course.number),
            asc(Offering.section),
        )
    elif field == 'title':
        query = query.order_by(
            asc(Offering.title),
        )
    elif field == 'units':
        query = query.order_by(
            asc(Offering.units),
        )
    elif field == 'instructors':
        query = query.order_by(
            asc(Person.id == None),
            asc(Person.last_name),
        )
    elif field == 'meetings':
        query = query.order_by(
            asc(TimeSlot.id == None),
            asc(func.substr(TimeSlot.weekdays, 1, 1)),
            asc(TimeSlot.start),
            asc(TimeSlot.end),
            asc(Room.id == None),
            asc(Building.name == None),
        )
    elif field == 'cores':
        query = query.order_by(
            asc(Core.id == None),
            asc(Core.code),
        )
    else:
        raise ValueError('invalid sorting key: {}'.format(field))
    return query
