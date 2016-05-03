#!/usr/bin/env python3

from csv import DictReader, QUOTE_NONE
from datetime import datetime
from functools import total_ordering
from os.path import dirname, join as join_path, realpath

DIRECTORY = dirname(realpath(__file__))

BUILDINGS_FILE = join_path(DIRECTORY, 'buildings.tsv')
CORES_FILE = join_path(DIRECTORY, 'cores.tsv')
DEPARTMENTS_FILE = join_path(DIRECTORY, 'departments.tsv')
OFFERINGS_FILE = join_path(DIRECTORY, 'offerings.tsv')

DATA_FILE = join_path(dirname(realpath(__file__)), 'counts.tsv')

def _multiton_canonicalize_key_(cls, args):
    assert len(args) >= len(cls.KEYS)
    key = tuple(args[:len(cls.KEYS)])
    if hasattr(cls, 'ALIASES'):
        key = tuple(cls.ALIASES.get(k, k) for k in key)
    return key

def _multiton_new_(cls, *args):
    key = cls._canonicalize_key_(tuple(args))
    if key not in cls.INSTANCES:
        cls.INSTANCES[key] = super(cls, cls).__new__(cls)
    return cls.INSTANCES[key]

def multiton(cls):
    if hasattr(cls, 'INSTANCES'):
        return cls
    setattr(cls, 'INSTANCES', {})
    setattr(cls, '__new__', _multiton_new_)
    setattr(cls, '_canonicalize_key_', classmethod(_multiton_canonicalize_key_))
    setattr(cls, 'get', classmethod(lambda cls, *args: cls.INSTANCES[cls._canonicalize_key_(tuple(args))]))
    setattr(cls, 'all', classmethod(lambda cls: cls.INSTANCES.values()))
    return cls

class AbstractMultiton:
    def __repr__(self):
        args = ', '.join('{}={}'.format(k, repr(getattr(self, k))) for k in type(self).KEYS)
        return '{}({})'.format(type(self).__name__, args)
    def __str__(self):
        return ' '.join(str(getattr(self, k)) for k in type(self).KEYS)

@total_ordering
@multiton
class Semester(AbstractMultiton):
    KEYS = ('year', 'season',)
    def __init__(self, year, season):
        self.year = year
        self.season = season
    @property
    def code(self):
        season = self.season.lower()
        if season == 'fall':
            return '{}01'.format(int(self.year) + 1)
        elif season == 'spring':
            return '{}02'.format(self.year)
        elif season == 'summer':
            return '{}03'.format(self.year)
    def __lt__(self, other):
        return self.code < other.code
    def __str__(self):
        return '{} {}'.format(self.year, self.season.capitalize())
    @staticmethod
    def current_semester():
        today = datetime.now()
        if today.month < 3 or (today.month == 3 and today.day < 15):
            year = today.year
            season = 'Spring'
        elif (today.month == 3 and today.day >= 15) or 4 <= today.month < 11:
            year = str(today.year)
            season = 'Fall'
        else:
            year = str(today.year + 1)
            season = 'Spring'
        return Semester(year, season)

@total_ordering
@multiton
class Weekday(AbstractMultiton):
    KEYS = ('weekday',)
    ALIASES = {
        'M': 'Monday',
        'T': 'Tuesday',
        'W': 'Wednesday',
        'R': 'Thursday',
        'F': 'Friday',
        'U': 'Saturday',
    }
    WEEKDAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday')
    ABBRS = {
        'Monday': 'M',
        'Tuesday': 'T',
        'Wednesday': 'W',
        'Thursday': 'R',
        'Friday': 'F',
        'Saturday': 'U',
    }
    def __init__(self, weekday):
        weekday = self._canonicalize_key_(tuple(weekday,))[0]
        assert weekday in Weekday.WEEKDAYS, weekday
        self.weekday = weekday
    @property
    def abbreviation(self):
        return Weekday.ABBRS[self.weekday]
    def __lt__(self, other):
        return Weekday.WEEKDAYS.index(self.weekday) < Weekday.WEEKDAYS.index(other.weekday)

@total_ordering
@multiton
class TimeSlot(AbstractMultiton):
    KEYS = ('weekdays', 'start_time', 'end_time',)
    def __init__(self, weekdays, start_time, end_time):
        self.weekdays = weekdays
        self.start_time = start_time
        self.end_time = end_time
    @property
    def weekdays_abbreviation(self):
        return ''.join(weekday.abbreviation for weekday in self.weekdays)
    @property
    def weekdays_str(self):
        return ', '.join(weekday.weekday for weekday in self.weekdays)
    @property
    def start_end(self):
        return (self.start_time.strftime('%I:%M%p') + '-' + self.end_time.strftime('%I:%M%p')).lower()
    def __lt__(self, other):
        return (self.weekdays, self.start_time, self.end_time) < (other.weekdays, other.start_time, other.end_time)
    def __str__(self):
        return '{} {}-{}'.format(''.join(day.abbreviation for day in self.weekdays), self.start_time.strftime('%H:%M'), self.end_time.strftime('%H:%M'))

@multiton
class Building(AbstractMultiton):
    KEYS = ('code',)
    def __init__(self, code, name):
        self.code = code
        self.name = name
    def __str__(self):
        return self.name

@multiton
class Room(AbstractMultiton):
    KEYS = ('building', 'room',)
    def __init__(self, building, room):
        self.building = building
        self.room = room

@total_ordering
@multiton
class Meeting(AbstractMultiton):
    KEYS = ('time_slot', 'location')
    def __init__(self, time_slot, location):
        self.time_slot = time_slot
        self.location = location
    def __lt__(self, other):
        if self.time_slot is None and other.time_slot is not None:
            return False
        elif self.time_slot is not None and other.time_slot is None:
            return True
        else:
            return self.time_slot < other.time_slot
    def __str__(self):
        if self.time_slot is None:
            return 'TBD'
        elif self.location is None:
            return '{} (TBD)'.format(self.time_slot)
        else:
            return '{} ({})'.format(self.time_slot, self.location)

@multiton
class Core(AbstractMultiton):
    KEYS = ('code',)
    def __init__(self, code, name):
        self.code = code
        self.name = name

@multiton
class Department(AbstractMultiton):
    KEYS = ('code',)
    def __init__(self, code, name):
        self.code = code
        self.name = name

class Person(AbstractMultiton):
    KEYS = ('alias',)
    def __init__(self, alias, first_name, last_name):
        self.alias = alias
        self.first_name = first_name
        self.last_name = last_name
    @property
    def full_name(self):
        return '{} {}'.format(self.first_name, self.last_name)
    @property
    def email(self):
        return '{}@oxy.edu'.format(self.alias)
    def __str__(self):
        return '{}, {}'.format(self.last_name, self.first_name)

@multiton
class Faculty(Person):
    PREFERRED_NAMES = {
        'Alexander F. Day': ('Sasha', 'Day'),
        'Allison de Fren': ('Allison', 'de Fren'),
        'Ning Hui Li': ('Justin', 'Li'),
        'William Dylan Sabo': ('Dylan', 'Sabo'),
        'Aleksandra Sherman': ('Sasha', 'Sherman'),
        'Charles Potts': ('Brady', 'Potts'),
        'Amanda J. Zellmer McCormack': ('Amanda J.', 'Zellmer'),
    }
    @property
    def first_last(self):
        return self.first_name + ' ' + self.last_name
    @property
    def last_first(self):
        return self.last_name + ', ' + self.first_name
    def __init__(self, alias, first_name, last_name):
        super().__init__(alias, first_name, last_name)
        self.affiliations = []

@multiton
class Student(Person):
    def __init__(self, alias, first_name, last_name):
        super().__init__(alias, first_name, last_name)
        self.advisor = None
        self.majors = []
        self.minors = []

@multiton
class Course(AbstractMultiton):
    KEYS = ('department', 'number',)
    def __init__(self, department, number):
        self.department = department
        self.number = number
    @property
    def pure_number_str(self):
        return ''.join(c for c in self.number if c.isdigit())
    @property
    def pure_number_int(self):
        return int(''.join(c for c in self.number if c.isdigit()))

@multiton
class Offering(AbstractMultiton):
    KEYS = ('semester', 'course', 'section',)
    def __init__(self, semester, course, section, name, units, instructors=None, meetings=None, cores=None):
        self.semester = semester
        self.course = course
        self.section = section
        self.name = name
        self.units = units
        self.instructors = instructors
        self.meetings = meetings
        self.cores = cores
    def __str__(self):
        return super().__str__() + ': ' + self.name

def load_data():
    load_buildings()
    load_cores()
    load_departments()
    load_offerings()

def load_buildings():
    with open(BUILDINGS_FILE) as fd:
        for row in DictReader(fd, delimiter='\t'):
            Building(row['code'], row['name'])

def load_departments():
    with open(DEPARTMENTS_FILE) as fd:
        for row in DictReader(fd, delimiter='\t'):
            Department(row['code'], row['name'])

def load_cores():
    with open(CORES_FILE) as fd:
        for row in DictReader(fd, delimiter='\t'):
            Core(row['code'], row['name'])

def load_offerings():
    with open(OFFERINGS_FILE) as fd:
        for offering in DictReader(fd, delimiter='\t', quoting=QUOTE_NONE):
            semester = Semester(int(offering['year']), offering['season'].capitalize())
            meetings = []
            for meeting_str in offering['meetings'].split(';'):
                time_str, days_str, location_str = meeting_str.strip().split(' ', maxsplit=2)
                if time_str == 'Time-TBD' or days_str == 'Days-TBD':
                    timeslot = None
                    location = None
                else:
                    weekdays = tuple(Weekday(c) for c in days_str)
                    start_time_str, end_time_str = time_str.upper().split('-')
                    start_time = datetime.strptime(start_time_str, '%I:%M%p').time()
                    end_time = datetime.strptime(end_time_str, '%I:%M%p').time()
                    timeslot = TimeSlot(weekdays, start_time, end_time)
                    if location_str == 'Bldg-TBD':
                        location_str = None
                    else:
                        if len(location_str.split()) == 1 and location_str in ('AGYM', 'KECK', 'UEPI', 'MULLIN', 'BIRD', 'TENNIS', 'THORNE', 'FM', 'CULLEY', 'TREE', 'RUSH', 'LIB', 'HERR'):
                            building_str = location_str
                            room_str = None
                        else:
                            building_str, room_str = location_str.rsplit(' ', maxsplit=1)
                        building = Building.get(building_str)
                        location = Room(building, room_str)
                meeting = Meeting(timeslot, location)
                meetings.append(meeting)
            department = Department.get(offering['department'])
            instructors = []
            for instructor_str in offering['instructors'].split(';'):
                instructor_str = instructor_str.strip()
                if instructor_str == 'Instructor Unassigned':
                    instructor = None
                else:
                    if instructor_str in Faculty.PREFERRED_NAMES:
                        first_name, last_name = Faculty.PREFERRED_NAMES[instructor_str]
                    else:
                        first_name, last_name = instructor_str.rsplit(' ', maxsplit=1)
                    instructor = Faculty(instructor_str, first_name, last_name)
                instructors.append(instructor)
            course = Course(department, offering['number'])
            if offering['cores']:
                cores = tuple(Core.get(code.strip()) for code in offering['cores'].split(';'))
            else:
                cores = tuple()
            offering = Offering(semester, course, offering['section'], offering['title'], int(offering['units']), tuple(instructors), tuple(meetings), cores)
