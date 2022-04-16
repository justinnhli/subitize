"""Query functions for subitize."""

# pylint: disable = singleton-comparison

from datetime import datetime

from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import and_, or_, text, asc, desc, func

from .models import Semester, TimeSlot, Building, Room, Meeting, Core, Department, Course, Person, Offering
from .models import OfferingMeeting, OfferingCore, OfferingInstructor
from .models import CourseInfo


def create_query(session):
    """Create a blank query for course offerings.

    Arguments:
        session (Session): The sqlalchemy session to connect with.

    Returns:
        Query: An unfiltered sqlalchemy Query on distinct Offerings.
    """
    return session.query(Offering).distinct()


def filter_study_abroad(session, query=None):
    """Filter out study abroad offerings.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    return query.join(
        session.query(Course).join(Department).filter(
            Department.code != 'OXAB',
            Department.code.notilike('AB%'),
        ).subquery()
    )


def filter_by_semester(session, query=None, semester=None):
    """Select offerings from a specific semester.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        semester (str): The semester code. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    if semester is None:
        return query
    return query.join(
        session.query(Semester).filter(Semester.id == semester).subquery()
    )


def filter_by_department(session, query=None, department=None):
    """Select offerings from a specific department.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        department (str): The department code. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    if department is None:
        return query
    return query.join(
        session.query(Course).join(Department).filter(Department.code == department).subquery()
    )


def filter_by_number_str(session, query=None, number=None):
    """Select offerings with a specific exact "number".

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        number (str): The course number, including any letters.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    if number is None:
        return query
    return query.join(
        session.query(Course).filter(Course.number == number).subquery()
    )


def filter_by_number(session, query=None, minimum=None, maximum=None):
    """Select offerings between a range of numbers.

    Letters in course numbers are ignored.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        minimum (int): The minimum acceptable number, inclusive. Optional.
        maximum (int): The maximum acceptable number, inclusive. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    filters = []
    if minimum is not None:
        filters.append(Course.number_int >= minimum)
    if maximum is not None:
        filters.append(Course.number_int <= maximum)
    if filters:
        return query.join(
            session.query(Course).filter(*filters).subquery()
        )
    else:
        return query


def filter_by_section(session, query=None, section=None):
    """Select offerings of a specific section.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        section (str): The section ID.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    if section is None:
        return query
    return query.filter(Offering.section == section)


def filter_by_units(session, query=None, units=None):
    """Select offerings worth a specific number of units.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        units (int): The number of units. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    if units is None:
        return query
    return query.filter(Offering.units == units)


def filter_by_instructor(session, query=None, instructor=None):
    """Select offerings taught by a specific instructor.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        instructor (str): The system name of the instructor. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    if instructor is None:
        return query
    return query.join(
        session.query(OfferingInstructor).join(Person).filter(Person.system_name == instructor).subquery()
    )


def filter_by_meeting(session, query=None, days=None, starts_after=None, ends_before=None):
    """Select offerings that meet on specific days and times.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        days (str): The concatenated one-letter abbreviation of the weekdays. Optional.
        starts_after (str): The earliest acceptable start time, inclusive. Optional.
        ends_before (str): The latest acceptable end time, inclusive. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    filters = []
    if days is not None:
        filters.append(or_(
            TimeSlot.weekdays == None,
            and_(*[TimeSlot.weekdays.ilike('%' + day + '%') for day in days]),
        ))
    if starts_after is not None:
        filters.append(or_(
            TimeSlot.start == None,
            TimeSlot.start >= datetime.strptime(starts_after, '%H%M').time(),
        ))
    if ends_before is not None:
        filters.append(or_(
            TimeSlot.end == None,
            TimeSlot.end <= datetime.strptime(ends_before, '%H%M').time(),
        ))
    if filters:
        offering_outer_alias = aliased(Offering)
        offering_inner_alias = aliased(Offering)
        offering_meeting_alias = aliased(OfferingMeeting)
        defined_subquery = session.query(offering_outer_alias.id.label('meeting_filtered_offering_id')).join(
            session.query(OfferingMeeting).outerjoin(Meeting, TimeSlot).filter(*filters).subquery()
        )
        undefined_subquery = (
            session.query(offering_inner_alias.id.label('meeting_filtered_offering_id'))
            .outerjoin(offering_meeting_alias)
            .filter(offering_meeting_alias.id == None)
        )
        subquery = defined_subquery.union(undefined_subquery).subquery('meeting_filtered')
        query = query.join(subquery, subquery.c.meeting_filtered_offering_id == Offering.id)
    return query


def filter_by_core(session, query=None, core=None):
    """Select offerings by core requirement fulfilled.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        core (str): The core requirement code. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    if core is None:
        return query
    return query.join(
        session.query(OfferingCore).join(Core).filter(Core.code == core).subquery()
    )


def filter_by_openness(session, query=None):
    """Select offerings that are open to enrollment.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    return query.filter(and_(Offering.num_waitlisted == 0, text('num_enrolled < num_seats - num_reserved')))


def filter_by_search(session, query=None, terms=None):
    """Select offerings that match search terms.

    Specifically, this function searches the following fields:
    * the course offering title
    * the department code (exact match)
    * the department name
    * the course number
    * the core requirement code (exact match)
    * the core requirement name
    * the instructor

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on. Optional.
        terms (str): A space-separated string of search terms. Optional.

    Returns:
        Query: A filtered sqlalchemy Query.
    """
    if query is None:
        query = create_query(session)
    if terms is None:
        return query
    for index, term in enumerate(terms.split(), start=1):
        offering_alias = aliased(Offering)
        subquery_alias = 'search_subquery_{}'.format(index)
        subquery = (session.query(offering_alias)
            .join(Course, Department)
            .outerjoin(OfferingCore, Core)
            .outerjoin(OfferingInstructor, Person)
            .filter(or_(
                offering_alias.title.ilike('%{}%'.format(term)),
                Department.code == term.upper(),
                Department.name.ilike('%{}%'.format(term)),
                Course.number == term.upper(),
                Course.number.ilike('%{}%'.format(term)),
                Core.code == term.upper(),
                Core.name.ilike('%{}%'.format(term)),
                Person.system_name.ilike('%{}%'.format(term)),
                Person.first_name.ilike('%{}%'.format(term)),
                Person.last_name.ilike('%{}%'.format(term)),
            )).subquery(subquery_alias))
        query = query.join(subquery, subquery.c.id == Offering.id)
    return query


def sort_offerings(session, query, field=None):
    """Sort the results of a query.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        query (Query): The existing query to build on.
        field (str): The sorting order. Must be one of [semester, course,
            title, units, instructors, meetings, cores]. Defaults to 'semester'.

    Returns:
        Query: A filtered sqlalchemy Query.

    Raises:
        ValueError: If the field is invalid.
    """
    if query is None:
        query = create_query(session)
    query = query.join(Semester)
    query = query.join(Course, Department)
    query = query.outerjoin(CourseInfo)
    query = query.outerjoin(OfferingMeeting, Meeting, TimeSlot, Room, Building)
    query = query.outerjoin(OfferingCore, Core)
    query = query.outerjoin(OfferingInstructor, Person)
    if field is None or field == 'semester':
        query = query.order_by(
            desc(Semester.id),
            asc(Department.name),
            asc(Course.number_int),
            asc(Course.number),
            asc(Offering.section),
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
            asc(Core.code),
        )
    else:
        raise ValueError('invalid sorting key: {}'.format(field))
    return query
