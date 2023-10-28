"""Query functions for subitize."""

# pylint: disable = singleton-comparison

from datetime import datetime

from sqlalchemy import select, union
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import and_, or_, asc, desc, func

from .models import Semester, TimeSlot, Building, Room, Meeting, Core, Department, Course, Person, Offering
from .models import OfferingMeeting, OfferingCore, OfferingInstructor


def create_select():
    """Create a blank query for course offerings.

    Returns:
        Query: An unfiltered sqlalchemy Query on distinct Offerings.
    """
    return select(Offering).distinct()


def filter_study_abroad(statement):
    """Filter out study abroad offerings.

    Arguments:
        statement (Select): The existing query to build on.

    Returns:
        Statement: The filtered Statement.
    """
    return statement.join(
        select(Course)
        .join(Department)
        .where(Department.code != 'OXAB')
        .where(Department.code.notilike('AB%'))
        .subquery()
    )


def filter_by_semester(statement, semester=None):
    """Select offerings from a specific semester.

    Arguments:
        statement (Select): The existing query to build on.
        semester (str): The semester code. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    if semester is None:
        return statement
    return statement.join(
        select(Semester)
        .where(Semester.id == semester)
        .subquery()
    )


def filter_by_department(statement, department=None):
    """Select offerings from a specific department.

    Arguments:
        statement (Select): The existing query to build on.
        department (str): The department code. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    if department is None:
        return statement
    return statement.join(
        select(Course)
        .join(Department)
        .where(Department.code == department)
        .subquery()
    )


def filter_by_number_str(statement, number=None):
    """Select offerings with a specific exact "number".

    Arguments:
        statement (Select): The existing query to build on.
        number (str): The course number, including any letters.

    Returns:
        Statement: The filtered Statement.
    """
    if number is None:
        return statement
    return statement.join(
        select(Course)
        .where(Course.number == number)
        .subquery()
    )


def filter_by_number(statement, minimum=None, maximum=None):
    """Select offerings between a range of numbers.

    Letters in course numbers are ignored.

    Arguments:
        statement (Select): The existing query to build on.
        minimum (int): The minimum acceptable number, inclusive. Optional.
        maximum (int): The maximum acceptable number, inclusive. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    conditions = []
    if minimum is not None:
        conditions.append(Course.number_int >= minimum)
    if maximum is not None:
        conditions.append(Course.number_int <= maximum)
    if conditions:
        return statement.join(select(Course).where(*conditions).subquery())
    else:
        return statement


def filter_by_section(statement, section=None):
    """Select offerings of a specific section.

    Arguments:
        statement (Select): The existing query to build on.
        section (str): The section ID. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    if section is None:
        return statement
    return statement.where(Offering.section == section)


def filter_by_units(statement, units=None):
    """Select offerings worth a specific number of units.

    Arguments:
        statement (Select): The existing query to build on.
        units (int): The number of units. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    if units is None:
        return statement
    return statement.where(Offering.units == units)


def filter_by_instructor(statement, instructor=None):
    """Select offerings taught by a specific instructor.

    Arguments:
        statement (Select): The existing query to build on.
        instructor (str): The system name of the instructor. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    if instructor is None:
        return statement
    return statement.join(
        select(OfferingInstructor)
        .join(Person)
        .where(Person.system_name == instructor)
        .subquery()
    )


def filter_by_meeting(statement, days=None, starts_after=None, ends_before=None):
    """Select offerings that meet on specific days and times.

    Arguments:
        statement (Select): The existing query to build on.
        days (str): The concatenated one-letter abbreviation of the weekdays. Optional.
        starts_after (str): The earliest acceptable start time, inclusive. Optional.
        ends_before (str): The latest acceptable end time, inclusive. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    if days is None and starts_after is None and ends_before is None:
        return statement
    conditions = []
    if days is not None:
        conditions.append(or_(
            TimeSlot.weekdays == '',
            and_(*[TimeSlot.weekdays.ilike('%' + day + '%') for day in days]),
        ))
    if starts_after is not None:
        conditions.append(or_(
            TimeSlot.start == None,
            TimeSlot.start >= datetime.strptime(starts_after, '%H%M').time(),
        ))
    if ends_before is not None:
        conditions.append(or_(
            TimeSlot.end == None,
            TimeSlot.end <= datetime.strptime(ends_before, '%H%M').time(),
        ))
    if conditions:
        subquery = (
            select(OfferingMeeting)
            .join(Meeting, isouter=True)
            .join(TimeSlot, isouter=True)
            .where(*conditions)
        )
        statement = statement.where(Offering.id.in_(
            union(
                # offerings that have a meeting (and meet the criteria)
                select(Offering.id).join(subquery.subquery()),
                # offerings that have no meetings (ie. are TBD)
                select(Offering.id).where(Offering.id.not_in(select(OfferingMeeting.offering_id))),
            )
        ))
    return statement


def filter_by_core(statement, core=None):
    """Select offerings by core requirement fulfilled.

    Arguments:
        statement (Select): The existing query to build on.
        core (str): The core requirement code. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    if core is None:
        return statement
    return statement.join(
        select(OfferingCore)
        .join(Core)
        .where(Core.code == core)
        .subquery()
    )


def filter_by_openness(statement):
    """Select offerings that are open to enrollment.

    Arguments:
        statement (Select): The existing query to build on.

    Returns:
        Statement: The filtered Statement.
    """
    return (
        statement
        .where(Offering.num_waitlisted == 0)
        .where(Offering.num_enrolled < Offering.num_seats - Offering.num_reserved)
    )


def filter_by_search(statement, terms=None):
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
        statement (Select): The existing query to build on.
        terms (str): A space-separated string of search terms. Optional.

    Returns:
        Statement: The filtered Statement.
    """
    if terms is None:
        return statement
    for term in terms.split():
        offering_alias = aliased(Offering)
        subquery = (
            select(offering_alias)
            .join(Course)
            .join(Department)
            .join(OfferingCore, isouter=True)
            .join(Core, isouter=True)
            .join(OfferingInstructor, isouter=True)
            .join(Person, isouter=True)
            .where(or_(
                offering_alias.title.ilike(f'%{term}%'),
                Department.code == term.upper(),
                Department.name.ilike(f'%{term}%'),
                Course.number == term.upper(),
                Course.number.ilike(f'%{term}%'),
                Core.code == term.upper(),
                Core.name.ilike(f'%{term}%'),
                Person.system_name.ilike(f'%{term}%'),
                Person.first_name.ilike(f'%{term}%'),
                Person.last_name.ilike(f'%{term}%'),
            )).subquery())
        statement = statement.join(subquery, subquery.c.id == Offering.id)
    return statement


def sort_offerings(statement, field=None):
    """Sort the results of a query.

    Arguments:
        statement (Select): The existing query to build on.
        field (str): The sorting order. Must be one of [semester, course,
            title, units, instructors, meetings, cores]. Defaults to 'semester'.

    Returns:
        Statement: The filtered Statement.

    Raises:
        ValueError: If the field is invalid.
    """
    if field is None or field == 'semester':
        return (
            statement
            .join(Semester)
            .join(Course)
            .join(Department)
            .order_by(
                desc(Semester.id),
                asc(Department.name),
                asc(Course.number_int),
                asc(Course.number),
                asc(Offering.section),
            )
        )
    elif field == 'course':
        return (
            statement
            .join(Course)
            .join(Department)
            .order_by(
                asc(Department.code),
                asc(Course.number_int),
                asc(Course.number),
                asc(Offering.section),
            )
        )
    elif field == 'title':
        return statement.order_by(asc(Offering.title))
    elif field == 'units':
        return statement.order_by(asc(Offering.units))
    elif field == 'instructors':
        return (
            statement
            .join(OfferingInstructor, isouter=True)
            .join(Person, isouter=True)
            .order_by(
                asc(Person.id == None),
                asc(Person.last_name),
            )
        )
    elif field == 'meetings':
        return (
            statement
            .join(OfferingMeeting, isouter=True)
            .join(Meeting, isouter=True)
            .join(TimeSlot, isouter=True)
            .join(Room, isouter=True)
            .join(Building, isouter=True)
            .order_by(
                asc(TimeSlot.id == None),
                asc(func.substr(TimeSlot.weekdays, 1, 1)),
                asc(TimeSlot.start),
                asc(TimeSlot.end),
                asc(Room.id == None),
                asc(Building.name == None),
            )
        )
    elif field == 'cores':
        return (
            statement
            .join(OfferingCore, isouter=True)
            .join(Core, isouter=True)
            .order_by(asc(Core.code))
        )
    else:
        raise ValueError(f'invalid sorting key: {field}')
        return statement # pylint: disable = unreachable
