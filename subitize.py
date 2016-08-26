#!/usr/bin/env python3

from argparse import ArgumentParser

from models import Semester, Offering
from subitizelib import filter_study_abroad, filter_by_search, filter_by_semester, sort_offerings

OFFERINGS = filter_study_abroad(tuple(Offering.all()))

def search(offerings, terms, sort=None):
    offerings = filter_by_search(offerings, terms)
    offerings = sort_offerings(offerings, sort)
    for offering in offerings:
        print('\t'.join((
            str(offering.semester),
            str(offering.course),
            str(offering.section),
            offering.name,
            str(offering.units),
            ', '.join(sorted(instructor.last_name for instructor in offering.instructors)),
            ', '.join(sorted(str(meeting) for meeting in offering.meetings)),
            (', '.join(sorted(str(core) for core in offering.cores)) if offering.cores else 'N/A'),
            str(offering.num_seats),
            str(offering.num_enrolled),
            str(offering.num_reserved),
            str(offering.num_reserved_open),
            str(offering.num_waitlisted),
        )))

def main():
    semester_choices = ('any', *sorted((semester.code for semester in Semester.all()), reverse=True))
    arg_parser = ArgumentParser()
    arg_parser.add_argument('terms', metavar='TERM', nargs='*')
    arg_parser.add_argument('--semester', default=Semester.current_semester().code, choices=semester_choices)
    arg_parser.add_argument('--sort', choices=('semester', 'number', 'title', 'instructors', 'meetings'))
    args = arg_parser.parse_args()
    if args.semester == 'any':
        offerings = OFFERINGS
    else:
        semester = Semester.from_code(args.semester)
        offerings = filter_by_semester(OFFERINGS, semester.code)
    search(offerings, ' '.join(args.terms), sort=args.sort)

if __name__ == '__main__':
    main()
