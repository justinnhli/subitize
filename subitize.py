#!/usr/bin/env python3

from argparse import ArgumentParser

from models import Semester, Offering, load_data
from subitizelib import filter_study_abroad, filter_by_search, filter_by_semester, sort_offerings

load_data()

OFFERINGS = filter_study_abroad(tuple(Offering.all()))

def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument('terms', metavar='TERM', nargs='*')
    arg_parser.add_argument('--semester', default=Semester.current_semester().code)
    arg_parser.add_argument('--sort', choices=('semester', 'number', 'title', 'instructors', 'meetings'))
    args = arg_parser.parse_args()
    if args.semester != 'any':
        semester = Semester.from_code(args.semester)
        offerings = filter_by_semester(OFFERINGS, semester.code)
    else:
        offerings = OFFERINGS
    offerings = filter_by_search(offerings, ' '.join(args.terms))
    offerings = sort_offerings(offerings, args.sort)
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

if __name__ == '__main__':
    main()
