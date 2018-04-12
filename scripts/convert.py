#!/usr/bin/env python3

from csv import DictReader, QUOTE_NONE
from os.path import join as join_path, realpath, dirname

sys.path.insert(0, dirname(dirname(realpath(__file__))))

from subitize import create_session
from update import create_objects # FIXME

OFFERINGS_FILE = join_path(dirname(realpath(__file__)), 'offerings.tsv')


def update_from_csv(session, file):
    with open(file) as fd:
        for csv_row in DictReader(fd, delimiter='\t', quoting=QUOTE_NONE):
            semester = [int(csv_row['year']), csv_row['season'].title()]
            department_code = csv_row['department']
            number = csv_row['number']
            section = csv_row['section']
            title = csv_row['title']
            units = csv_row['units']
            instructors = [
                instructor.strip() for instructor in csv_row['instructors'].split(';')
                if 'Instructor Unassigned' not in instructor
            ]
            meetings = [meeting.strip().split(' ', maxsplit=2) for meeting in csv_row['meetings'].split(';')]
            meetings = [[text.strip() for text in meeting] for meeting in meetings]
            cores = [core.strip() for core in csv_row['cores'].split(';')]
            cores = [core for core in cores if core]
            num_enrolled = int(csv_row['enrolled'])
            num_seats = int(csv_row['seats'])
            num_reserved = int(csv_row['reserved'])
            num_reserved_open = int(csv_row['reserved_open'])
            num_waitlisted = int(csv_row['waitlisted'])
            create_objects(
                session, semester, department_code, number, section, title, units, instructors, meetings, cores,
                num_seats, num_enrolled, num_reserved, num_reserved_open, num_waitlisted
            )


def main():
    session = create_session()
    update_from_csv(session, OFFERINGS_FILE)
    session.commit()


if __name__ == '__main__':
    main()
