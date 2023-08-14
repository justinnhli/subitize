#!/usr/bin/env python3
"""remove any unused instances in the DB."""

import sys
from os.path import dirname, realpath

ROOT_DIRECTORY = dirname(dirname(realpath(__file__)))
sys.path.insert(0, ROOT_DIRECTORY)

from subitize import create_session
from subitize import Semester, TimeSlot, Building, Room, Meeting
from subitize import Core, Department, Course, Person
from subitize import OfferingMeeting, OfferingCore, OfferingInstructor, Offering
from subitize import CourseDescription


def delete_orphans(session):
    """Delete unreferenced objects.

    Arguments:
        session (Session): The DB connection session.
    """
    # pylint: disable=too-many-branches, too-many-statements

    for course in session.query(Course).all():
        referenced = (
            session.query(Offering).filter(Offering.course == course).first()
            or session.query(CourseDescription).filter(CourseDescription.course == course).first()
        )
        if not referenced:
            print('Course {} is never referenced; deleting...'.format(course))
            session.delete(course)
    for department in session.query(Department).all():
        if not session.query(Course).filter(Course.department == department).first():
            print('Department {} is never referenced; deleting...'.format(department))
            session.delete(department)

    for offering_instructor in session.query(OfferingInstructor).all():
        if not session.query(Offering).filter(Offering.id == offering_instructor.offering_id).first():
            print('OfferingInstructor {} is never referenced; deleting...'.format(offering_instructor))
            session.delete(offering_instructor)
    for person in session.query(Person).all():
        if not session.query(OfferingInstructor).filter(OfferingInstructor.instructor_id == person.id).first():
            print('Person {} is never referenced; deleting...'.format(person))
            session.delete(person)

    for offering_core in session.query(OfferingCore).all():
        if not session.query(Offering).filter(Offering.id == offering_core.offering_id).first():
            print('OfferingCore {} is never referenced; deleting...'.format(offering_core))
            session.delete(offering_core)
    for core in session.query(Core).all():
        if not session.query(OfferingCore).filter(OfferingCore.core_code == core.code).first():
            print('Core {} is never referenced; deleting...'.format(core))
            session.delete(core)

    for offering_meeting in session.query(OfferingMeeting).all():
        if not session.query(Offering).filter(Offering.id == offering_meeting.offering_id).first():
            print('OfferingMeeting {} is never referenced; deleting...'.format(offering_meeting))
            session.delete(offering_meeting)
    for meeting in session.query(Meeting).all():
        if not session.query(OfferingMeeting).filter(OfferingMeeting.meeting_id == meeting.id).first():
            print('Meeting {} is never referenced; deleting...'.format(meeting))
            session.delete(meeting)
    for room in session.query(Room).all():
        if not session.query(Meeting).filter(Meeting.room == room).first():
            print('Room {} is never referenced; deleting...'.format(room))
            session.delete(room)
    for building in session.query(Building).all():
        if not session.query(Room).filter(Room.building == building).first():
            print('Building {} is never referenced; deleting...'.format(building))
            session.delete(building)
    for timeslot in session.query(TimeSlot).all():
        if not session.query(Meeting).filter(Meeting.timeslot == timeslot).first():
            print('Timeslot {} is never referenced; deleting...'.format(timeslot))
            session.delete(timeslot)

    for semester in session.query(Semester).all():
        if not session.query(Offering).filter(Offering.semester == semester).first():
            print('Semester {} is never referenced; deleting...'.format(semester))
            session.delete(semester)


def check_children(session):
    """Assert referenced members of all objects exist.

    Arguments:
        session (Session): The DB connection session.
    """
    for offering in session.query(Offering).all():
        semester = session.query(Semester).get(offering.semester_id)
        assert semester, 'Cannot find semester of {}'.format(offering)
        course = session.query(Course).get(offering.course_id)
        assert course, 'Cannot find course of {}'.format(offering)
        department = session.query(Department).get(course.department_code)
        assert department, 'Cannot find department of {}'.format(course)

    for offering_meeting in session.query(OfferingMeeting).all():
        offering = session.query(Offering).get(offering_meeting.offering_id)
        assert offering, 'Cannot find offering of {}'.format(offering_meeting)
        meeting = session.query(Meeting).get(offering_meeting.meeting_id)
        assert meeting, 'Cannot find meeting of {}'.format(offering_meeting)
        if meeting.timeslot_id:
            timeslot = session.query(TimeSlot).get(meeting.timeslot_id)
            assert timeslot, 'Cannot find timeslot of {}'.format(meeting)
        if meeting.room_id:
            room = session.query(Room).get(meeting.room_id)
            assert room, 'Cannot find room of {}'.format(meeting)
            building = session.query(Building).get(room.building_code)
            assert building, 'Cannot find building of {}'.format(room)

    for offering_instructor in session.query(OfferingInstructor).all():
        offering = session.query(Offering).get(offering_instructor.offering_id)
        assert offering, 'Cannot find offering of {}'.format(offering_instructor)
        instructor = session.query(Person).get(offering_instructor.instructor_id)
        assert instructor, 'Cannot find instructor of {}'.format(offering_instructor)

    for offering_core in session.query(OfferingCore).all():
        offering = session.query(Offering).get(offering_core.offering_id)
        assert offering, 'Cannot find offering of {}'.format(offering_core)
        core = session.query(Core).get(offering_core.core_code)
        assert core, 'Cannot find instructor of {}'.format(offering_core)

    for course_desc in session.query(CourseDescription).all():
        course = session.query(Course).get(course_desc.course_id)
        assert course, 'Cannot find course of {}'.format(course_desc)


def main():
    """Remove any unused instances in the DB."""
    session = create_session()
    delete_orphans(session)
    check_children(session)
    session.commit()


if __name__ == '__main__':
    main()
