"""Database models for subitize."""

import sqlite3
from datetime import datetime, date
from pathlib import Path
from time import sleep

from sqlalchemy import create_engine, event, select
from sqlalchemy import Integer, String, Time, ForeignKey
from sqlalchemy.orm import DeclarativeBase, mapped_column, relationship, Session
from sqlalchemy.schema import UniqueConstraint

DATA_DIR = Path(__file__).resolve().parent / 'data'
DB_PATH = DATA_DIR / 'counts.db'
SQL_PATH = DATA_DIR / 'data.sql'

SQLITE_URI = f'sqlite:///{DB_PATH}'

ENGINE = create_engine(SQLITE_URI)
event.listen(ENGINE, 'connect', (lambda dbapi_con, con_record: dbapi_con.execute('pragma foreign_keys=ON')))


class Base(DeclarativeBase):
    """The base model class."""
    pass


class Semester(Base):
    """An academic semester."""

    __tablename__ = 'semesters'
    __table_args__ = (
        UniqueConstraint('year', 'season', name='_year_season_uc'),
    )
    id = mapped_column(Integer, primary_key=True)
    year = mapped_column(Integer, nullable=False)
    season = mapped_column(String, nullable=False)

    def __init__(self, year, season):
        """Initialize the semester.

        Arguments:
            year (int): The calendar year of the semester.
            season (str): The season. Must be one of [fall, spring, summer].
        """
        self.year = year
        self.season = season
        self.id = int(self.code)

    @property
    def code(self):
        """Get the Oxy code for the semester."""
        season = self.season.lower()
        if season == 'fall':
            return f'{int(self.year)+1}01'
        elif season == 'spring':
            return f'{self.year}02'
        elif season == 'summer':
            return f'{self.year}03'
        assert False
        return None

    def __str__(self):
        return f'{self.year} {self.season}'

    def __lt__(self, other):
        return self.code < other.code

    @staticmethod
    def current_semester_code():
        """Get the semester code for the "current" semester.

        The current semester is determined by hard cutoffs:

        * If it is before March 22, return the spring semester.
        * If it is before October 15, return the fall semester.
        * Otherwise, return the next spring semester.

        Returns:
            str: The semester code.

        """
        today = datetime.today().date()
        if today < date(today.year, 3, 22):
            return str(today.year) + '02'
        elif today < date(today.year, 10, 15):
            return str(today.year + 1) + '01'
        else:
            return str(today.year + 1) + '02'

    @staticmethod
    def code_to_season(code):
        """Convert a semester code to a (year, season) pair.

        Arguments:
            code (str): The semester code.

        Returns:
            list: The integer year and titlized season.

        Raises:
            ValueError: If the semester code is invalid.
        """
        year = int(code[:4])
        season = code[-2:]
        if season == '01':
            return year - 1, 'Fall'
        elif season == '02':
            return year, 'Spring'
        elif season == '03':
            return year, 'Summer'
        raise ValueError(f'invalid semester code: {code}')


class TimeSlot(Base):
    """A class meeting weekly time slot."""

    ALIASES = [
        ['M', 'Monday'],
        ['T', 'Tuesday'],
        ['W', 'Wednesday'],
        ['R', 'Thursday'],
        ['F', 'Friday'],
        ['U', 'Saturday'],
    ]
    __tablename__ = 'timeslots'
    __table_args__ = (
        UniqueConstraint('weekdays', 'start', 'end', name='_weekdays_time_uc'),
    )
    id = mapped_column(Integer, primary_key=True)
    weekdays = mapped_column(String, nullable=False)
    start = mapped_column(Time, nullable=False)
    end = mapped_column(Time, nullable=False)

    def __str__(self):
        return f'{self.weekdays} {self.us_start_time}-{self.us_end_time}'

    @property
    def weekdays_names(self):
        """Get the weekdays on which this TimeSlot meets.

        Returns:
            str: A comma-separated list of weekday names.
        """
        return ', '.join(name for abbr, name in TimeSlot.ALIASES if abbr in self.weekdays)

    @property
    def iso_start_time(self):
        """Get the start time of this TimeSlot in 24 hour format.

        Returns:
            str: The start time.
        """
        return self.start.strftime('%H:%M')

    @property
    def iso_end_time(self):
        """Get the end time of this TimeSlot in 24 hour format.

        Returns:
            str: The end time.
        """
        return self.end.strftime('%H:%M')

    @property
    def us_start_time(self):
        """Get the start time of this TimeSlot in 12 hour format.

        Returns:
            str: The start time.
        """
        return self.start.strftime('%I:%M%p').strip('0').lower()

    @property
    def us_end_time(self):
        """Get the end time of this TimeSlot in 12 hour format.

        Returns:
            str: The end time.
        """
        return self.end.strftime('%I:%M%p').strip('0').lower()


class Building(Base):
    """A building."""

    __tablename__ = 'buildings'
    code = mapped_column(String, primary_key=True, nullable=False)
    name = mapped_column(String, nullable=False)

    def __str__(self):
        return f'{self.name} ({self.code})'


class Room(Base):
    """A room within a building."""

    __tablename__ = 'rooms'
    __table_args__ = (
        UniqueConstraint('building_code', 'room', name='_building_room_uc'),
    )
    id = mapped_column(Integer, primary_key=True)
    building_code = mapped_column(String, ForeignKey('buildings.code'), nullable=False)
    building = relationship('Building')
    room = mapped_column(String, nullable=True)

    def __str__(self):
        return f'{self.building.code} {self.room}'


class Meeting(Base):
    """A meeting of a course offering.

    A meeting consists of a TimeSlot and Room. Both of these could be null/None
    if they are yet to be determined.
    """

    __tablename__ = 'meetings'
    id = mapped_column(Integer, primary_key=True)
    timeslot_id = mapped_column(Integer, ForeignKey('timeslots.id'), nullable=True)
    room_id = mapped_column(Integer, ForeignKey('rooms.id'), nullable=True)
    timeslot = relationship('TimeSlot')
    room = relationship('Room')

    def __str__(self):
        return f'{self.timeslot} ({self.room})'

    @property
    def weekdays(self):
        """Shortcut for TimeSlot.weekdays.

        Returns:
            str: The concatenated one-letter abbreviation of the weekdays.
        """
        return self.timeslot.weekdays

    @property
    def weekdays_names(self):
        """Shortcut for TimeSlot.weekdays_names.

        Returns:
            str: A comma-separated list of weekday names.
        """
        return self.timeslot.weekdays_names

    @property
    def iso_start_time(self):
        """Shortcut for TimeSlot.iso_start_time.

        Returns:
            str: The start time.
        """
        return self.timeslot.iso_start_time

    @property
    def iso_end_time(self):
        """Shortcut for TimeSlot.iso_end_time.

        Returns:
            str: The end time.
        """
        return self.timeslot.iso_end_time

    @property
    def us_start_time(self):
        """Shortcut for TimeSlot.us_start_time.

        Returns:
            str: The start time.
        """
        return self.timeslot.us_start_time

    @property
    def us_end_time(self):
        """Shortcut for TimeSlot.us_end_time.

        Returns:
            str: The end time.
        """
        return self.timeslot.us_end_time


class Core(Base):
    """A core requirement."""

    __tablename__ = 'cores'
    code = mapped_column(String, primary_key=True, nullable=False)
    name = mapped_column(String, nullable=False)

    def __str__(self):
        return f'{self.name} ({self.code})'


class Department(Base):
    """A course subject."""

    __tablename__ = 'departments'
    code = mapped_column(String, primary_key=True, nullable=False)
    name = mapped_column(String, nullable=False)

    def __str__(self):
        return f'{self.name} ({self.code})'


class Course(Base):
    """A course."""

    __tablename__ = 'courses'
    __table_args__ = (
        UniqueConstraint('department_code', 'number', name='_department_number_uc'),
    )
    id = mapped_column(Integer, primary_key=True)
    department_code = mapped_column(String, ForeignKey('departments.code'), nullable=False)
    number = mapped_column(String, nullable=False)
    number_int = mapped_column(Integer, nullable=False)
    department = relationship('Department')

    def __str__(self):
        return f'{self.department.code} {self.number}'


class Person(Base):
    """A person."""

    __tablename__ = 'people'
    id = mapped_column(Integer, primary_key=True)
    system_name = mapped_column(String, nullable=False)
    first_name = mapped_column(String, nullable=False)
    last_name = mapped_column(String, nullable=False)
    offerings = relationship('Offering', secondary='offering_instructor_assoc', back_populates='instructors')

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class OfferingMeeting(Base):
    """The many-to-many Offering-Meeting relation."""

    __tablename__ = 'offering_meeting_assoc'
    id = mapped_column(Integer, primary_key=True)
    offering_id = mapped_column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False, index=True)
    meeting_id = mapped_column(Integer, ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False, index=True)


class OfferingCore(Base):
    """The many-to-many Offering-Core relation."""

    __tablename__ = 'offering_core_assoc'
    id = mapped_column(Integer, primary_key=True)
    offering_id = mapped_column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False, index=True)
    core_code = mapped_column(String, ForeignKey('cores.code', ondelete='CASCADE'), nullable=False, index=True)


class OfferingInstructor(Base):
    """The many-to-many Offering-Person relation."""

    __tablename__ = 'offering_instructor_assoc'
    id = mapped_column(Integer, primary_key=True)
    offering_id = mapped_column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False, index=True)
    instructor_id = mapped_column(Integer, ForeignKey('people.id', ondelete='CASCADE'), nullable=False, index=True)


class Offering(Base):
    """A specific course offering."""

    __tablename__ = 'offerings'
    __table_args__ = (
        UniqueConstraint('semester_id', 'course_id', 'section', name='_semester_course_section_uc'),
    )
    id = mapped_column(Integer, primary_key=True)
    semester_id = mapped_column(Integer, ForeignKey('semesters.id'), nullable=False)
    semester = relationship('Semester')
    course_id = mapped_column(Integer, ForeignKey('courses.id'), nullable=False)
    course = relationship('Course')
    course_desc_id = mapped_column(Integer, ForeignKey('course_descriptions.id'), nullable=True)
    course_desc = relationship('CourseDescription')
    section = mapped_column(String, nullable=False)
    title = mapped_column(String, nullable=False)
    units = mapped_column(Integer, nullable=False)
    instructors = relationship('Person', secondary='offering_instructor_assoc', back_populates='offerings')
    meetings = relationship('Meeting', secondary='offering_meeting_assoc')
    cores = relationship('Core', secondary='offering_core_assoc')
    num_enrolled = mapped_column(Integer, nullable=False)
    num_seats = mapped_column(Integer, nullable=False)
    num_reserved = mapped_column(Integer, nullable=False)
    num_reserved_open = mapped_column(Integer, nullable=False)
    num_waitlisted = mapped_column(Integer, nullable=False)

    def __str__(self):
        return f'{self.semester} {self.course} {self.section}'

    @property
    def is_open(self):
        """Determine if the offering is open to enrollment.

        An offering is open if:

        * There is no one on the waitlist, and
        * The number of students enrolled is less than the number of non-reserved seats.

        Returns:
            bool: If the course is open.
        """
        return self.num_waitlisted == 0 and self.num_enrolled < self.num_seats - self.num_reserved

    @property
    def readable_id(self):
        """Create a unique ID for this offering.

        Returns:
            str: The unique ID.
        """
        parts = []
        parts.append(str(self.semester.code))
        parts.append(self.course.department.code)
        parts.append(self.course.number)
        parts.append(self.section)
        return '_'.join(parts)

    def to_json_dict(self):
        """Represent this offering in JSON-compatible dictionary.

        Returns:
            dict: The JSON-compatible dictionary.
        """
        result = {}
        result['id'] = self.readable_id
        result['semester'] = {
            'year': self.semester.year,
            'season': self.semester.season,
            'code': self.semester.code,
        }
        result['department'] = {
            'name': self.course.department.name,
            'code': self.course.department.code,
        }
        result['number'] = {
            'number': self.course.number_int,
            'string': self.course.number,
        }
        result['section'] = self.section
        result['title'] = self.title
        result['units'] = self.units
        result['instructors'] = []
        for instructor in self.instructors:
            result['instructors'].append({
                'first_name': instructor.first_name,
                'last_name': instructor.last_name,
                'system_name': instructor.system_name,
            })
        result['meetings'] = []
        for meeting in self.meetings:
            meeting_dict = {}
            if not meeting.timeslot:
                meeting_dict.update({
                    'weekdays': None,
                    'iso_start_time': None,
                    'iso_end_time': None,
                    'us_start_time': None,
                    'us_end_time': None,
                })
            else:
                meeting_dict.update({
                    'weekdays': {
                        'names': meeting.weekdays_names,
                        'codes': meeting.weekdays,
                    },
                    'iso_start_time': meeting.iso_start_time,
                    'iso_end_time': meeting.iso_end_time,
                    'us_start_time': meeting.us_start_time,
                    'us_end_time': meeting.us_end_time,
                })

            if not meeting.room:
                meeting_dict.update({
                    'building': None,
                    'room': None,
                })
            else:
                meeting_dict.update({
                    'building': {
                        'name': meeting.room.building.name,
                        'code': meeting.room.building.code,
                    },
                    'room': meeting.room.room,
                })
            result['meetings'].append(meeting_dict)
        result['cores'] = []
        for core in self.cores:
            result['cores'].append({
                'name': core.name,
                'code': core.code,
            })
        result['num_enrolled'] = self.num_enrolled
        result['num_seats'] = self.num_seats
        result['num_reserved'] = self.num_reserved
        result['num_reserved_open'] = self.num_reserved_open
        result['num_waitlisted'] = self.num_waitlisted
        if not self.course_desc:
            result['info'] = None
        else:
            result['info'] = {
                'description': self.course_desc.description,
                'prerequisites': self.course_desc.prerequisites,
                'corequisites': self.course_desc.corequisites,
                'url': self.course_desc.url,
            }
        return result


class CourseDescription(Base):
    """The catalog description of a course."""

    __tablename__ = 'course_descriptions'
    __table_args__ = (
        UniqueConstraint('year', 'course_id', name='_year_course_uc'),
    )
    id = mapped_column(Integer, primary_key=True)
    year = mapped_column(Integer, nullable=False)
    course_id = mapped_column(Integer, ForeignKey('courses.id'))
    url = mapped_column(String, nullable=False)
    description = mapped_column(String, nullable=True)
    prerequisites = mapped_column(String, nullable=True)
    corequisites = mapped_column(String, nullable=True)
    parsed_prerequisites = mapped_column(String, nullable=True)


def create_session():
    """Create a SQLAlchemy session.

    Returns:
        Session: A SQLAlchemy Session object.
    """
    return Session(ENGINE)


def create_db():
    """Read the dump into a binary SQLite file."""
    Base.metadata.create_all(ENGINE)
    done = False
    while not done:
        if not DB_PATH.exists():
            with SQL_PATH.open(encoding='utf-8') as fd:
                dump = fd.read()
            conn = sqlite3.connect(DB_PATH)
            try:
                with conn:
                    conn.executescript(dump)
            except sqlite3.OperationalError:
                pass
            conn.close()
        for _ in range(3):
            conn = sqlite3.connect(DB_PATH)
            try:
                with conn:
                    conn.execute('SELECT * FROM semesters')
                done = True
                break
            except sqlite3.OperationalError:
                sleep(1)
            conn.close()
        if not done:
            DB_PATH.unlink(missing_ok=True)


def get_or_create(session, model, **kwargs):
    """Retrieve or create an object from the database.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        model (class): The object class to retrieve or create.
        **kwargs (Filter): Arbitrary filters on the object.

    Returns:
        object: The first object that passes all filters.
    """
    instance = session.scalars(select(model).filter_by(**kwargs)).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        instance = session.scalars(select(model).filter_by(**kwargs)).first()
    assert instance is not None
    return instance


create_db()
