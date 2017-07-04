from datetime import datetime, date

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint

SQLITE_URI = 'sqlite:///counts.db'

def create_session(engine=None):
    if engine is None:
        engine = create_engine(SQLITE_URI, connect_args={'check_same_thread':False})
    event.listen(engine, 'connect', (lambda dbapi_con, con_record: dbapi_con.execute('pragma foreign_keys=ON')))
    Session = sessionmaker(bind=engine)
    return Session()

Base = declarative_base()

class Semester(Base):
    __tablename__ = 'semesters'
    __table_args__ = (
        UniqueConstraint('year', 'season', name='_year_season_uc'),
    )
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    season = Column(String, nullable=False)
    def __init__(self, year, season):
        self.year = year
        self.season = season
        self.id = int(self.code)
    @property
    def code(self):
        season = self.season.lower()
        if season == 'fall':
            return '{}01'.format(int(self.year) + 1)
        elif season == 'spring':
            return '{}02'.format(self.year)
        elif season == 'summer':
            return '{}03'.format(self.year)
    def __str__(self):
        return '{} {}'.format(self.year, self.season)
    def __lt__(self, other):
        return self.code < other.code
    def __repr__(self):
        return '<Semester(year={}, season="{}")>'.format(self.year, self.season)
    @staticmethod
    def current_semester(session=None):
        today = datetime.today().date()
        if today < date(today.year, 3, 15):
            year, season = today.year, 'Spring'
        elif today < date(today.year, 10, 15):
            year, season = today.year, 'Fall'
        else:
            year, season = today.year + 1, 'Spring'
        if session is None:
            session = create_session()
        return session.query(Semester).filter(Semester.year == year, Semester.season == season).one()
    @staticmethod
    def code_to_season(code):
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
        return '<TimeSlot(weekdays={}, start={}, end={})>'.format(self.weekdays, self.start.strftime('%H:%M'), self.end.strftime('%H:%M'))
    @property
    def weekdays_names(self):
        return ',' .join(name for abbr, name in TimeSlot.ALIASES if abbr in self.weekdays)
    @property
    def us_start_time(self):
        return self.start.strftime('%I:%M%p').strip('0').lower()
    @property
    def us_end_time(self):
        return self.end.strftime('%I:%M%p').strip('0').lower()

class Building(Base):
    __tablename__ = 'buildings'
    code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    def __repr__(self):
        return '<Building(code="{}")>'.format(self.code)

class Room(Base):
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
        return self.timeslot.weekdays
    @property
    def weekdays_names(self):
        return self.timeslot.weekdays_names
    @property
    def us_start_time(self):
        return self.timeslot.us_start_time
    @property
    def us_end_time(self):
        return self.timeslot.us_end_time

class Core(Base):
    __tablename__ = 'cores'
    code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    def __repr__(self):
        return '<Core(code="{}")>'.format(self.code)

class Department(Base):
    __tablename__ = 'departments'
    code = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    def __repr__(self):
        return '<Department(code="{}")>'.format(self.code)

class Course(Base):
    __tablename__ = 'courses'
    __table_args__ = (
        UniqueConstraint('department_code', 'number', name='_department_number_uc'),
    )
    id = Column(Integer, primary_key=True)
    department_code = Column(String, ForeignKey('departments.code'), nullable=False)
    number = Column(String, nullable=False)
    number_int = Column(Integer, nullable=False)
    department = relationship('Department')
    def __repr__(self):
        return '<Course(department="{}", number="{}")>'.format(self.department.code, self.number)

class Person(Base):
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True)
    system_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    offerings = relationship(
        'Offering',
        secondary='offering_instructor_assoc',
        back_populates='instructors'
    )
    def __str__(self):
        return '{}, {}'.format(self.last_name, self.first_name)

class OfferingMeeting(Base):
    __tablename__ = 'offering_meeting_assoc'
    id = Column(Integer, primary_key=True)
    offering_id = Column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False)
    meeting_id = Column(Integer, ForeignKey('meetings.id', ondelete='CASCADE'), nullable=False)

class OfferingCore(Base):
    __tablename__ = 'offering_core_assoc'
    id = Column(Integer, primary_key=True)
    offering_id = Column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False)
    core_code = Column(String, ForeignKey('cores.code', ondelete='CASCADE'), nullable=False)

class OfferingInstructor(Base):
    __tablename__ = 'offering_instructor_assoc'
    id = Column(Integer, primary_key=True)
    offering_id = Column(Integer, ForeignKey('offerings.id', ondelete='CASCADE'), nullable=False)
    instructor_id = Column(Integer, ForeignKey('people.id', ondelete='CASCADE'), nullable=False)

class Offering(Base):
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
    instructors = relationship(
        'Person',
        secondary='offering_instructor_assoc',
        back_populates='offerings')
    meetings = relationship(
        'Meeting',
        secondary='offering_meeting_assoc')
    cores = relationship(
        'Core',
        secondary='offering_core_assoc')
    num_enrolled = Column(Integer, nullable=False)
    num_seats = Column(Integer, nullable=False)
    num_reserved = Column(Integer, nullable=False)
    num_reserved_open = Column(Integer, nullable=False)
    num_waitlisted = Column(Integer, nullable=False)
    @property
    def is_open(self):
        return self.num_waitlisted == 0 and self.num_enrolled < self.num_seats - self.num_reserved

def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if not instance:
        instance = model(**kwargs)
        session.add(instance)
    assert instance is not None
    return instance
