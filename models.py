from csv import DictReader, QUOTE_NONE
from datetime import datetime, date
from functools import total_ordering
from os.path import dirname, join as join_path, realpath

DIRECTORY = join_path(dirname(realpath(__file__)), 'data')

BUILDINGS_FILE = join_path(DIRECTORY, 'buildings.tsv')
CORES_FILE = join_path(DIRECTORY, 'cores.tsv')
DEPARTMENTS_FILE = join_path(DIRECTORY, 'departments.tsv')
OFFERINGS_FILE = join_path(DIRECTORY, 'offerings.tsv')

DATA_FILE = join_path(dirname(realpath(__file__)), 'counts.tsv')

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
    return cls

class AbstractMultiton:
    def __repr__(self):
        args = ', '.join('{}={}'.format(k, repr(getattr(self, k))) for k in type(self).KEYS)
        return '{}({})'.format(type(self).__name__, args)
    def __str__(self):
        return ' '.join(str(getattr(self, k)) for k in type(self).KEYS)
    @classmethod
    def _canonicalize_key_(cls, args):
        assert len(args) >= len(cls.KEYS)
        key = tuple(args[:len(cls.KEYS)])
        if hasattr(cls, 'ALIASES'):
            key = tuple(cls.ALIASES.get(k, k) for k in key)
        return key
    @classmethod
    def all(cls):
        return cls.INSTANCES.values()
    @classmethod
    def get(cls, *args):
        return cls.INSTANCES[cls._canonicalize_key_(tuple(args))]

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
        today = datetime.today().date()
        if today < date(today.year, 3, 15):
            return Semester(today.year, 'Spring')
        elif today < date(today.year, 10, 15):
            return Semester(today.year, 'Fall')
        else:
            return Semester(today.year + 1, 'Spring')
    @staticmethod
    def from_code(code):
        year = int(code[:4])
        season = code[-2:]
        if season == '01':
            return Semester(year - 1, 'Fall')
        elif season == '02':
            return Semester(year, 'Spring')
        elif season == '03':
            return Semester(year, 'Summer')
        raise ValueError('invalid semester code: {}'.format(code))

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
    def us_start_time(self):
        return self.start_time.strftime('%I:%M%p').strip('0').lower()
    @property
    def us_end_time(self):
        return self.end_time.strftime('%I:%M%p').strip('0').lower()
    @property
    def iso_start_time(self):
        return self.start_time.strftime('%H:%M')
    @property
    def iso_end_time(self):
        return self.end_time.strftime('%H:%M')
    def __lt__(self, other):
        return (self.weekdays[0], self.start_time, self.end_time) < (other.weekdays[0], other.start_time, other.end_time)
    def __repr__(self):
        start_time = self.us_start_time
        if len(start_time) == 6:
            start_time = '0' + start_time
        end_time = self.us_end_time
        if len(end_time) == 6:
            end_time = '0' + end_time
        return '{}-{} {}'.format(start_time, end_time, ''.join(day.abbreviation for day in self.weekdays))
    def __str__(self):
        return '{} {}-{}'.format(''.join(day.abbreviation for day in self.weekdays), self.us_start_time, self.us_end_time)

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
    def __repr__(self):
        if self.room:
            return self.building.code + ' ' + self.room
        else:
            return self.building.code

@total_ordering
@multiton
class Meeting(AbstractMultiton):
    KEYS = ('time_slot', 'location')
    def __init__(self, time_slot, location):
        self.time_slot = time_slot
        self.location = location
    @property
    def weekdays(self):
        return self.time_slot.weekdays
    @property
    def start_time(self):
        return self.time_slot.start_time
    @property
    def end_time(self):
        return self.time_slot.end_time
    @property
    def weekdays_abbreviation(self):
        return self.time_slot.weekdays_abbreviation
    @property
    def weekdays_str(self):
        return self.time_slot.weekdays_str
    @property
    def us_start_time(self):
        return self.time_slot.us_start_time
    @property
    def us_end_time(self):
        return self.time_slot.us_end_time
    @property
    def iso_start_time(self):
        return self.time_slot.iso_start_time
    @property
    def iso_end_time(self):
        return self.time_slot.iso_end_time
    @property
    def building(self):
        return self.location.building
    @property
    def room(self):
        return self.location.room
    def __lt__(self, other):
        if self.time_slot is None and other.time_slot is not None:
            return False
        elif self.time_slot is not None and other.time_slot is None:
            return True
        else:
            return self.time_slot < other.time_slot
    def __repr__(self):
        if self.time_slot is None:
            return 'Time-TBD Days-TBD Bldg-TBD'
        elif self.location is None:
            return repr(self.time_slot) + ' Bldg-TBD'
        else:
            return '{} {}'.format(repr(self.time_slot), repr(self.location))
    def __str__(self):
        if self.time_slot is None:
            return 'TBD'
        elif self.location is None:
            return '{} (TBD)'.format(self.time_slot)
        else:
            return '{} ({})'.format(self.time_slot, self.location)
    @staticmethod
    def from_str(time_str, days_str, location_str):
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
                location = None
            elif len(location_str.split()) == 1 and location_str in ('AGYM', 'KECK', 'UEPI', 'MULLIN', 'BIRD', 'TENNIS', 'THORNE', 'FM', 'CULLEY', 'TREE', 'RUSH', 'LIB', 'HERR'):
                location = Room(Building.get(location_str), None)
            else:
                try:
                    building_str, room_str = location_str.rsplit(' ', maxsplit=1)
                    location = Room(Building.get(building_str), room_str)
                except ValueError:
                    location = None
        return Meeting(timeslot, location)

@multiton
class Core(AbstractMultiton):
    KEYS = ('code',)
    def __init__(self, code, name):
        self.code = code
        self.name = name

@total_ordering
@multiton
class Department(AbstractMultiton):
    KEYS = ('code',)
    def __init__(self, code, name):
        self.code = code
        self.name = name
    def __lt__(self, other):
        return self.code < other.code

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
    def __repr__(self):
        return self.alias
    @staticmethod
    def split_name(alias):
        if alias in Faculty.PREFERRED_NAMES:
            return Faculty.PREFERRED_NAMES[alias]
        else:
            return alias.rsplit(' ', maxsplit=1)

@multiton
class Student(Person):
    def __init__(self, alias, first_name, last_name):
        super().__init__(alias, first_name, last_name)
        self.advisor = None
        self.majors = []
        self.minors = []

@total_ordering
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
    def __lt__(self, other):
        return (self.department.code, self.number) < (other.department.code, other.number)

@multiton
class Offering(AbstractMultiton):
    KEYS = ('semester', 'course', 'section',)
    def __init__(self, semester, course, section, name, units, instructors=None, meetings=None, cores=None, seats=0, enrolled=0, reserved=0, reserved_open=0, waitlisted=0):
        self.semester = semester
        self.course = course
        self.section = section
        self.name = name
        self.units = units
        self.instructors = instructors
        self.meetings = meetings
        self.cores = cores
        self.num_enrolled = enrolled
        self.num_seats = seats
        self.num_reserved = reserved
        self.num_reserved_open = reserved_open
        self.num_waitlisted = waitlisted
    @property
    def year(self):
        return self.semester.year
    @property
    def season(self):
        return self.semester.season
    @property
    def department(self):
        return self.course.department
    @property
    def number(self):
        return self.course.number
    @property
    def is_open(self):
        return self.num_waitlisted == 0 and self.num_enrolled < self.num_seats - self.num_reserved
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

def load_offering(offering):
    semester = Semester(int(offering['year']), offering['season'].capitalize())
    meetings = []
    for meeting_str in offering['meetings'].split(';'):
        try:
            time_str, days_str, location_str = meeting_str.strip().split(' ', maxsplit=2)
            meeting = Meeting.from_str(time_str, days_str, location_str)
        except ValueError:
            meeting = Meeting(None, None)
        meetings.append(meeting)
    department = Department.get(offering['department'])
    instructors = []
    for instructor_str in offering['instructors'].split(';'):
        instructor_str = instructor_str.strip()
        if instructor_str == 'Instructor Unassigned':
            instructor = None
        else:
            instructor = Faculty(instructor_str, *Faculty.split_name(instructor_str))
        instructors.append(instructor)
    course = Course(department, offering['number'])
    if offering['cores']:
        cores = tuple(Core.get(code.strip()) for code in offering['cores'].split(';'))
    else:
        cores = tuple()
    return Offering(semester, course, offering['section'], offering['title'], int(offering['units']), tuple(instructors), tuple(meetings), cores, int(offering['seats']), int(offering['enrolled']), int(offering['reserved']), int(offering['reserved_open']), int(offering['waitlisted']))

def load_offerings():
    with open(OFFERINGS_FILE) as fd:
        for offering in DictReader(fd, delimiter='\t', quoting=QUOTE_NONE):
            load_offering(offering)

load_data()
