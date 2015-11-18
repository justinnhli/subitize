#!/usr/bin/env python3

# TODO
# the problem here is that there are two purposes this script could be used for
# the first is to find a list of courses for some purpose (advising, instructor schedule, etc.)
# the second is to get the set of background knowledge (list of instructors, list of departments, etc.)
# in theory, the second doesn't require a query at all - the KB just needs to be updated every semester

from csv import reader as csv_reader
from datetime import datetime

DAY_ABBRS = {
    'monday': 'M',
    'tuesday': 'T',
    'wednesday': 'W',
    'thursday': 'R',
    'friday': 'F',
}

CORE_ABBRS = {
    'CPAF': 'Core Africa &amp; The Middle East',
    'CPAS': 'Core Central/South/East Asia',
    'CPEU': 'Core Europe',
    'CPFA': 'Core Fine Arts',
    'CFAP': 'Core Fine Arts Partial',
    'CPGC': 'Core Global Connections',
    'CPIC': 'Core Intercultural',
    'CPLS': 'Core Laboratory Science',
    'CPLA': 'Core Latin America',
    'CMSP': 'Core Math/Science Partial',
    'CPMS': 'Core Mathematics/Science',
    'CPPE': 'Core Pre-1800',
    'CPRF': 'Core Regional Focus',
    'CPUS': 'Core United States',
    'CPUD': 'Core United States Diversity',
}

DEPARTMENT_ABBRS = {
    'AMST': 'American Studies',
    'ARAB': 'Arabic',
    'ARTH': 'Art History and Visual Arts/Art History',
    'ARTM': 'Art History and Visual Arts/Media Arts and Culture',
    'ARTS': 'Art History and Visual Arts/Studio Art',
    'BICH': 'Biochemistry',
    'BIO': 'Biology',
    'CHEM': 'Chemistry',
    'CHIN': 'Chinese',
    'CLAS': 'Classical Studies',
    'COGS': 'Cognitive Science',
    'CSLC': 'Comparative Studies in Literature and Culture',
    'COMP': 'Computer Science',
    'CTSJ': 'Critical Theory and Social Justice',
    'CSP': 'Cultural Studies Program',
    'DWA': 'Diplomacy and World Affairs',
    'ECLS': 'English and Comparative Literary Studies',
    'ECON': 'Economics',
    'EDUC': 'Education',
    'ENGL': 'English',
    'ENWR': 'English Writing',
    'FREN': 'French',
    'GEO': 'Geology',
    'GERM': 'German',
    'GRK': 'Greek',
    'HIST': 'History',
    'ITAL': 'Italian',
    'JAPN': 'Japanese',
    'KINE': 'Kinesiology',
    'LANG': 'Language',
    'LATN': 'Latin',
    'LLAS': 'Latino/a and Latin American Studies',
    'LING': 'Linguistics',
    'MATH': 'Mathematics',
    'MUSC': 'Music',
    'MUSA': 'Music Applied Study',
    'PHIL': 'Philosophy',
    'PHAC': 'Physical Activities',
    'PHYS': 'Physics',
    'POLS': 'Politics',
    'PSYC': 'Psychology',
    'RELS': 'Religious Studies',
    'RUSN': 'Russian',
    'SOC': 'Sociology',
    'SPAN': 'Spanish and French Studies',
    'THEA': 'Theater',
    'UEP': 'Urban and Environmental Policy',
    'WRD': 'Writing and Rhetoric',
}

class Course:
    def __init__(self, department, number):
        self.department = department
        self.number = number
    def __str__(self):
        return self.department + ' ' + self.number

class Meeting:
    def __init__(self, time, days, location):
        self.start_time = None
        self.end_time = None
        if time != 'Time-TBD':
            start_time, end_time = time.upper().split('-')
            self.start_time = datetime.strptime(start_time, '%I:%M%p')
            self.end_time = datetime.strptime(end_time, '%I:%M%p')
        self.days = days
        self.location = location
    def __str__(self):
        start_time = (self.start_time.strftime('%I:%M%p') if self.start_time else 'Time-TBD')
        end_time = (self.end_time.strftime('%I:%M%p') if self.end_time else 'Time-TBD')
        return '{}-{} {} {}'.format(start_time, end_time, self.days, self.location)
    @staticmethod
    def from_string(s):
        return Meeting(*s.split(' ', maxsplit=2))

class Offering:
    def __init__(self, year, season, course, section, title, units, instructors, meetings, core, seats, enrolled, reserved, reserved_open, waitlist):
        self.year = year
        self.season = season
        self.course = course
        self.section = section
        self.title = title
        self.units = units
        self.instructors = instructors
        self.meetings = meetings
        self.core = core
        self.seats = seats
        self.enrolled = enrolled
        self.reserved = reserved
        self.reserved_open = reserved_open
        self.waitlist = waitlist
    def tsv_row(self):
        values = []
        values.append(self.year)
        values.append(self.season)
        values.append(str(self.course))
        values.append(self.section)
        values.append(self.title)
        values.append(self.units)
        values.append('; '.join(self.instructors))
        values.append('; '.join(str(meeting) for meeting in self.meetings))
        values.append('; '.join(sorted(self.core)))
        values.append(self.seats)
        values.append(self.enrolled)
        values.append(self.reserved)
        values.append(self.reserved_open)
        values.append(self.waitlist)
        return '\t'.join(values)

def date_to_season(month, date):
    if month < 5:
        return 'Spring'
    elif 5 < month < 8:
        return 'Summer'
    elif 8 < month:
        return 'Fall'
    elif month == 5:
        if date < 15:
            return 'Spring'
        else:
            return 'Summer'
    elif month == 8:
        if date < 15:
            return 'Summer'
        else:
            return 'Fall'

def read_data():
    offerings = []
    with open('counts.tsv') as fd:
        fd.readline()
        for offering in csv_reader(fd, delimiter='\t'):
            year, season, department, number, section, title, units, instructors, meetings, core, seats, enrolled, reserved, reserved_open, waitlisted = offering
            course = Course(department, number)
            instructors = tuple(instructor.strip() for instructor in instructors.split(';'))
            meetings = tuple(Meeting.from_string(meeting) for meeting in meetings.split(';'))
            core = core.split(';')
            offerings.append(Offering(year, season, course, section, title, units, instructors, meetings, core, seats, enrolled, reserved, reserved_open, waitlisted))
    return offerings

def main():
    from argparse import ArgumentParser
    offerings = read_data()
    arg_parser = ArgumentParser()
    arg_parser.add_argument('--year')
    arg_parser.add_argument('--season', choices=('fall', 'spring', 'summer'))
    arg_parser.add_argument('--department')
    arg_parser.add_argument('--number')
    arg_parser.add_argument('--min-number')
    arg_parser.add_argument('--max-number')
    arg_parser.add_argument('--title')
    arg_parser.add_argument('--units')
    arg_parser.add_argument('--min-units')
    arg_parser.add_argument('--max-units')
    arg_parser.add_argument('--instructor')
    arg_parser.add_argument('--core')
    arg_parser.add_argument('--time')
    arg_parser.add_argument('--day')
    arg_parser.add_argument('--building')
    arg_parser.add_argument('--room')
    args = arg_parser.parse_args()
    filters = []
    if args.year:
        filters.append((lambda offering: args.year == offering.year))
    if args.season:
        filters.append((lambda offering: args.season.lower() == offering.season.lower()))
    if args.department:
        filters.append((lambda offering: args.department.lower() == offering.course.department.lower() or args.department.lower() in DEPARTMENT_ABBRS[offering.course.department].lower()))
    if args.number:
        filters.append((lambda offering: args.number == offering.course.number))
    if args.min_number:
        filters.append((lambda offering: args.min_number <= offering.course.number))
    if args.max_number:
        filters.append((lambda offering: args.max_number >= offering.course.number))
    if args.title:
        filters.append((lambda offering: args.title.lower() in offering.title.lower()))
    if args.units:
        filters.append((lambda offering: args.units == offering.units))
    if args.min_units:
        filters.append((lambda offering: args.min_units <= offering.units))
    if args.max_units:
        filters.append((lambda offering: args.max_units >= offering.units))
    if args.instructor:
        filters.append((lambda offering: any((args.instructor.lower() in instructor.lower()) for instructor in offering.instructors)))
    if args.core:
        filters.append((lambda offering: any((core != 'N/A' and (args.core.lower() == core.lower() or args.core.lower() in CORE_ABBRS[core].lower())) for core in offering.core)))
    if args.time:
        try:
            time = datetime.strptime(args.time.upper(), '%I:%M%p')
        except ValueError:
            arg_parser.error('argument --time: time must be in HH:MMxm format')
        filters.append((lambda offering: any(meeting.start_time < time < meeting.end_time for meeting in offering.meetings if meeting.start_time is not None)))
    if args.day:
        if args.day.lower() in DAY_ABBRS:
            args.day = DAY_ABBRS[args.day.lower()]
        filters.append((lambda offering: any((args.day.upper() in meeting.days) for meeting in offering.meetings)))
    if args.building:
        filters.append((lambda offering: any((args.building.lower() in meeting.location.lower()) for meeting in offering.meetings)))
    if args.room:
        filters.append((lambda offering: any((args.room.lower() in meeting.location.lower()) for meeting in offering.meetings)))
    for offering in offerings:
        if all(fn(offering) for fn in filters):
            print(offering.tsv_row())

if __name__ == '__main__':
    main()
