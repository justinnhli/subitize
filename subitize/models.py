"""Database models for subitize."""

import sqlite3
from datetime import datetime, date
from os.path import dirname, exists as file_exists, join as join_path
from time import sleep

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

DIR_PATH = dirname(__file__)
DB_PATH = join_path(DIR_PATH, 'data', 'counts.db')
SQL_PATH = join_path(DIR_PATH, 'data', 'data.sql')

SQLITE_URI = 'sqlite:///' + join_path(DIR_PATH, DB_PATH)


def create_db():
    """Read the dump into a binary SQLite file."""
    if not file_exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open(SQL_PATH) as fd:
            dump = fd.read()
        conn.executescript(dump)
        conn.commit()
        conn.close()
    assert file_exists(DB_PATH)
    while True:
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.execute('SELECT * FROM semesters')
            break
        except sqlite3.OperationalError:
            sleep(1)


create_db()
ENGINE = create_engine(SQLITE_URI, connect_args={'check_same_thread': False})


def create_session(engine=None):
    """Create a sqlalchemy session.

    Arguments:
        engine (Engine): The database engine. Optional.

    Returns:
        Session: A sqlalchemy Session object.
    """
    create_db()
    if engine is None:
        engine = ENGINE
    event.listen(engine, 'connect', (lambda dbapi_con, con_record: dbapi_con.execute('pragma foreign_keys=ON')))
    return sessionmaker(bind=engine)()


Base = declarative_base(ENGINE) # pylint: disable = invalid-name


class Semester(Base):
    """An academic semester."""

    __tablename__ = 'semesters'
    __table_args__ = (
        UniqueConstraint('year', 'season', name='_year_season_uc'),
    )
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    season = Column(String, nullable=False)

    def __init__(self, year, season):
        """Constructor.

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
            return '{}01'.format(int(self.year) + 1)
        elif season == 'spring':
            return '{}02'.format(self.year)
        elif season == 'summer':
            return '{}03'.format(self.year)
        assert False
        return None

    def __str__(self):
        return '{} {}'.format(self.year, self.season)

    def __lt__(self, other):
        return self.code < other.code

    def __repr__(self):
        return '<Semester(year={}, season="{}")>'.format(self.year, self.season)

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
        raise ValueError('invalid semester code: {}'.format(code))


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
    id = Column(Integer, primary_key=True)
    weekdays = Column(String, nullable=False)
    start = Column(Time, nullable=False)
    end = Column(Time, nullable=False)

    def __str__(self):
        return '{} {}-{}'.format(self.weekdays, self.us_start_time, self.us_end_time)

    def __repr__(self):
        return '<TimeSlot(weekdays={}, start={}, end={})>'.format(
            self.weekdays, self.start.strftime('%H:%M'), self.end.strftime('%H:%M')
        )

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
    code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

    def __repr__(self):
        return '<Building(code="{}")>'.format(self.code)


class Room(Base):
    """A room within a building."""

    __tablename__ = 'rooms'
    __table_args__ = (
        UniqueConstraint('building_code', 'room', name='_building_room_uc'),
    )
    id = Column(Integer, primary_key=True)
    building_code = Column(String, ForeignKey('buildings.code'), nullable=False)
    building = relationship('Building')
    room = Column(String, nullable=True)

    def __str__(self):
        return '{} {}'.format(self.building.code, self.room)

    def __repr__(self):
        return '<Room(building="{}", room="{}")>'.format(self.building.code, self.room)


class Meeting(Base):
    """A meeting of a course offering.

    A meeting consists of a TimeSlot and Room. Both of these could be null/None
    if they are yet to be determined.
    """

    __tablename__ = 'meetings'
    id = Column(Integer, primary_key=True)
    timeslot_id = Column(Integer, ForeignKey('timeslots.id'), nullable=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=True)
    timeslot = relationship('TimeSlot')
    room = relationship('Room')

    def __str__(self):
        return '{} ({})'.format(str(self.timeslot), str(self.room))

    def __repr__(self):
        return '<Meeting(UGH)>'

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
    code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

    def __repr__(self):
        return '<Core(code="{}")>'.format(self.code)


class Department(Base):
    """A course subject."""

    __tablename__ = 'departments'
    code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)

    def __str__(self):
        return '{} ({})'.format(self.name, self.code)

    def __repr__(self):
        return '<Department(code="{}")>'.format(self.code)


class Course(Base):
    """A course."""

    __tablename__ = 'courses'
    __table_args__ = (
        UniqueConstraint('department_code', 'number', name='_department_number_uc'),
    )
    id = Column(Integer, primary_key=True)
    department_code = Column(String, ForeignKey('departments.code'), nullable=False)
    number = Column(String, nullable=False)
    number_int = Column(Integer, nullable=False)
    department = relationship('Department')
    info = relationship('CourseInfo', back_populates='course', uselist=False)

    def __str__(self):
        return '{} {}'.format(self.department.code, self.number)

    def __repr__(self):
        return '<Course(department="{}", number="{}")>'.format(self.department.code, self.number)


class Person(Base):
    """A person."""

    __tablename__ = 'people'
    id = Column(Integer, primary_key=True)
    system_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    offerings = relationship('Offering', secondary='offering_instructor_assoc', back_populates='instructors')

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class OfferingMeeting(Base):
    """The many-to-many Offering-Meeting relation."""

    __tablename__ = 'offering_meeting_assoc'
    id = Column(Integer, primary_key=True)
    offering_id = Column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False, index=True)
    meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False, index=True)


class OfferingCore(Base):
    """The many-to-many Offering-Core relation."""

    __tablename__ = 'offering_core_assoc'
    id = Column(Integer, primary_key=True)
    offering_id = Column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False, index=True)
    core_code = Column(String, ForeignKey('cores.code', ondelete='CASCADE'), nullable=False, index=True)


class OfferingInstructor(Base):
    """The many-to-many Offering-Person relation."""

    __tablename__ = 'offering_instructor_assoc'
    id = Column(Integer, primary_key=True)
    offering_id = Column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False, index=True)
    instructor_id = Column(Integer, ForeignKey('people.id', ondelete='CASCADE'), nullable=False, index=True)


class Offering(Base):
    """A specific course offering."""

    __tablename__ = 'offerings'
    __table_args__ = (
        UniqueConstraint('semester_id', 'course_id', 'section', name='_semester_course_section_uc'),
    )
    id = Column(Integer, primary_key=True)
    semester_id = Column(Integer, ForeignKey('semesters.id'), nullable=False)
    semester = relationship('Semester')
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False)
    course = relationship('Course')
    section = Column(String, nullable=False)
    title = Column(String, nullable=False)
    units = Column(Integer, nullable=False)
    instructors = relationship('Person', secondary='offering_instructor_assoc', back_populates='offerings')
    meetings = relationship('Meeting', secondary='offering_meeting_assoc')
    cores = relationship('Core', secondary='offering_core_assoc')
    num_enrolled = Column(Integer, nullable=False)
    num_seats = Column(Integer, nullable=False)
    num_reserved = Column(Integer, nullable=False)
    num_reserved_open = Column(Integer, nullable=False)
    num_waitlisted = Column(Integer, nullable=False)

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
        if not self.course.info:
            result['info'] = None
        else:
            result['info'] = {
                'description': self.course.info.description,
                'prerequisites': self.course.info.prerequisites,
                'corequisites': self.course.info.corequisites,
                'url': self.course.info.url,
            }
        return result


class CourseInfo(Base):
    """Metadata about a course."""

    __tablename__ = 'course_info'
    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    course = relationship('Course', back_populates='info', uselist=False)
    url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    prerequisites = Column(String, nullable=True)
    corequisites = Column(String, nullable=True)
    parsed_prerequisites = Column(String, nullable=True)

    def __repr__(self):
        return '_'.join(s for s in [self.url, self.description, self.prerequisites, self.corequisites] if s is not None)


def get_or_create(session, model, **kwargs):
    """Retrieve or create an object from the database.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        model (class): The object class to retrieve or create.
        **kwargs (Filter): Arbitrary filters on the object.

    Returns:
        object: The first object that passes all filters.
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
        instance = session.query(model).filter_by(**kwargs).first()
    assert instance is not None
    return instance
