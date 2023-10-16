#!/usr/bin/env python3

import re
import sys
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from os import chdir
from subprocess import run
from urllib.parse import urlsplit, urljoin

import requests
from bs4 import BeautifulSoup, Comment

ROOT_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIRECTORY))

from subitize import create_db, create_session, get_or_create
from subitize import Semester, TimeSlot, Building, Room, Meeting
from subitize import Core, Department, Course, Person
from subitize import OfferingMeeting, OfferingCore, OfferingInstructor, Offering
from subitize import CourseDescription
from subitize import create_query, filter_by_semester, filter_by_department, filter_by_number_str, filter_by_section

DB_PATH = ROOT_DIRECTORY / 'subitize' / 'data' / 'counts.db'
DUMP_PATH = ROOT_DIRECTORY / 'subitize' / 'data' / 'data.sql'
SCHEMA_PATH = ROOT_DIRECTORY / 'subitize' / 'data' / 'schema.sql'
LAST_UPDATE_PATH = ROOT_DIRECTORY / 'subitize' / 'data' / 'last-update'
COURSE_COUNTS = 'https://counts.oxy.edu/public/default.aspx'

CATALOG_URL = 'https://oxy.smartcatalogiq.com/en/{}-{}/catalog/'
CATALOG_CACHE_PATH = Path(__file__).resolve().parent / 'catalog-cache'
REQUEST_HEADERS = {
    #'Host':'counts.oxy.edu',
    'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:42.0) Gecko/20100101 Firefox/42.0',
    'Accept':'*/*',
    'Accept-Encoding':'gzip, deflate, br',
    'Accept-Language':'en-US,en;q=0.5',
    'X-Requested-With':'XMLHttpRequest',
    'X-MicrosoftAjax':'Delta=true',
    'Cache-Control':'no-cache',
    'Content-Type':'application/x-www-form-urlencoded; charset=utf-8',
    'DNT':'1',
    #'Referer':'https://counts.oxy.edu/public/default.aspx',
    'Connection':'keep-alive',
}

PREFERRED_NAMES = {
    'Allison de Fren': ('Allison', 'de Fren'),
    'Amanda J. Zellmer McCormack': ('Amanda J.', 'Zellmer'),
    'Justin de Leon': ('Justin', 'de Leon'),
    'To the Estate of Deborah Martinson': ('Deborah', 'Martinson'),
    'Carey Sargent': ('Jacob', 'Sargent'),
}


# utility functions


def get_url(url):
    headers = dict(REQUEST_HEADERS)
    headers['Host'] = urlsplit(url).netloc
    headers['Referer'] = url
    response = requests.get(url.lower(), headers=headers)
    assert response.status_code == 200, f'Downloading {url} resulted in HTTP status {response.status_code}'
    return response.text


def get_soup_from_url(url):
    return BeautifulSoup(get_url(url), 'html.parser')


def get_catalog_url(year):
    return CATALOG_URL.format(year - 1, year)


def get_courses_urls(year):
    visited_urls = set()
    catalog_url = get_catalog_url(year)
    catalog_soup = get_soup_from_url(catalog_url)
    for link in catalog_soup.select('div.toc > ul > li > a'):
        if 'Course' not in link.get_text():
            continue
        depts_soup = get_soup_from_url(urljoin(CATALOG_URL, link['href']))
        for dept_link_soup in depts_soup.select('.sc-child-item-links li a'):
            dept_courses_soup = get_soup_from_url(urljoin(CATALOG_URL, dept_link_soup['href']))
            for course_link_soup in dept_courses_soup.select('#main ul li a'):
                course_url = urljoin(CATALOG_URL, course_link_soup['href'])
                if course_url in visited_urls:
                    continue
                visited_urls.add(course_url)
                yield course_url


def clean_soup(soup):
    for tag in soup.select('a'):
        tag.unwrap()
    changed = True
    while changed:
        changed = False
        for tag in soup.select('*'):
            if tag.string and not tag.string.strip():
                tag.extract()
                changed = True
    for tag in soup.find_all(text=lambda text: isinstance(text, Comment)):
        tag.extract()
    return soup


# catalog functions


def extract_section(section):
    heading = section.contents[0].get_text().strip()
    body = ' '.join(str(contents) for contents in section.contents[1:]).strip()
    return heading, body


def extract_basic_info(session, course_soup):
    dept, number = course_soup.select('h1')[0].get_text().split(' ')[:2]
    dept = dept.strip()
    number = number.strip()
    department = get_or_create(session, Department, code=dept)
    description = str(clean_soup(course_soup.select('div.desc')[0]).unwrap())
    if description:
        description = re.sub(r'\s+', ' ', description)
    else:
        description = None
    return department, number, description


def extract_prerequisites(course_soup):
    contents = str(course_soup.select('#main')[0])
    sections = []
    last_pos = 0
    for match in re.finditer('<h[2-6]>', contents.lower()):
        section_soup = BeautifulSoup(contents[last_pos:match.start()], 'html.parser')
        if section_soup.get_text().strip():
            sections.append(section_soup)
        last_pos = match.start()
    sections.append(BeautifulSoup(contents[last_pos:], 'html.parser'))
    prerequisites = None
    corequisites = None
    for section_soup in sections[1:]:
        children = [tag for tag in section_soup.contents if hasattr(tag, 'strings') or tag.strip()]
        if len(children) >= 2:
            key, body = extract_section(section_soup)
            if key == 'Prerequisite':
                prerequisites = str(clean_soup(BeautifulSoup(body, 'html.parser')))
                prerequisites = re.sub(r'\s+', ' ', prerequisites)
            elif key == 'Corequisite':
                corequisites = str(clean_soup(BeautifulSoup(body, 'html.parser')))
                corequisites = re.sub(r'\s+', ' ', corequisites)
    return prerequisites, corequisites


def parse_prerequisites(prerequisites):
    return None # TODO


def extract_course_info(session, year, url, html):
    course_soup = BeautifulSoup(html, 'html.parser')
    department, number, description = extract_basic_info(session, course_soup)
    prerequisites, corequisites = extract_prerequisites(course_soup)
    # parsed_prerequisites = parse_prerequisites(prerequisites) # FIXME
    for number in re.split('[/-]', number):
        number = number.strip()
        if not number:
            continue
        # FIXME check whether the description has changed from the most recent catalog first
        course = get_or_create(
            session, Course, department=department, number=number, number_int=int(re.sub('[^0-9]', '', number))
        )
        course_desc = session.query(CourseDescription).filter(
            CourseDescription.year == year,
            CourseDescription.course_id == course.id,
        ).first()
        if course_desc:
            course_desc.url = url
        else:
            course_desc = get_or_create(session, CourseDescription, year=year, course_id=course.id, url=url)
        course_desc.description = description
        course_desc.prerequisites = prerequisites
        course_desc.corequisites = corequisites
        course_desc.parsed_prerequisites = parsed_prerequisites
        # TODO detect if prerequisites have changed


def update_course_info(year):
    year_cache_path = CATALOG_CACHE_PATH / str(year)
    # download all urls
    for course_url in get_courses_urls(year):
        cache_path = (year_cache_path / urlsplit(course_url).path[1:]).with_suffix('.html')
        if cache_path.exists():
            continue
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open('w', encoding='utf-8') as fd:
            fd.write(get_url(course_url))
            fd.write('\n')
    # scape and save into DB
    session = create_session()
    for path in sorted(year_cache_path.glob('**/*.html')):
        course_url = urljoin(CATALOG_URL, '/' + str(path.relative_to(year_cache_path)))
        with path.open(encoding='utf-8') as fd:
            extract_course_info(session, year, course_url, fd.read())
        break
    session.commit()
    dump()


# offering functions


def create_department(session, code):
    department = session.query(Department).filter_by(code=code).first()
    if not department:
        department = Department(code=code, name='FIXME')
        session.add(department)
        print(f'created unnamed department with code {code}')
    return department


def create_instructor(session, system_name):
    system_name = system_name.strip()
    if system_name == 'Instructor Unassigned':
        return None
    instructor = session.query(Person).filter_by(system_name=system_name)
    if instructor.count() == 0:
        if system_name in PREFERRED_NAMES:
            first_name, last_name = PREFERRED_NAMES[system_name]
            system_name = f'{first_name} {last_name}'
        else:
            first_name, last_name = system_name.rsplit(' ', maxsplit=1)
        return get_or_create(session, Person, system_name=system_name, first_name=first_name, last_name=last_name)
    elif instructor.count() == 1:
        return instructor.first()
    assert False
    return None


def create_room(session, location_str):
    if location_str == 'Bldg-TBD':
        room = None
    elif ' ' not in location_str:
        building = get_or_create(session, Building, code=location_str)
        room = get_or_create(session, Room, building=building, room=None)
    else:
        building_str, room_str = location_str.rsplit(' ', maxsplit=1)
        building = get_or_create(session, Building, code=building_str)
        room = get_or_create(session, Room, building=building, room=room_str)
    return room


def create_meeting(session, meeting_strs):
    if len(meeting_strs) == 2:
        time_str, days_str = meeting_strs
        location_str = 'Bldg-TBD'
    else:
        time_str, days_str, location_str = meeting_strs
    if time_str == 'Time-TBD' or days_str == 'Days-TBD':
        timeslot = None
        room = None
    else:
        start_time_str, end_time_str = time_str.upper().split('-')
        start_time = datetime.strptime(start_time_str, '%I:%M%p').time()
        end_time = datetime.strptime(end_time_str, '%I:%M%p').time()
        timeslot = get_or_create(session, TimeSlot, weekdays=days_str, start=start_time, end=end_time)
        room = create_room(session, location_str)
    if timeslot is None:
        return None
    else:
        return get_or_create(session, Meeting, timeslot=timeslot, room=room)


def create_objects(
        session, semester, department_code, number, section, title, units, instructors, meetings, cores,
        num_seats, num_enrolled, num_reserved, num_reserved_open, num_waitlisted):
    semester = get_or_create(session, Semester, year=semester[0], season=semester[1])
    department = create_department(session, department_code)
    course = get_or_create(
        session, Course, department=department, number=number, number_int=int(re.sub('[^0-9]', '', number))
    )
    instructors = [create_instructor(session, instructor) for instructor in instructors]
    instructors = [instructor for instructor in instructors if instructor is not None]
    meetings = [create_meeting(session, meeting) for meeting in meetings]
    meetings = [meeting for meeting in meetings if meeting is not None]
    cores = [get_or_create(session, Core, code=core) for core in cores]
    offering = session.query(Offering).filter_by(semester=semester, course=course, section=section)
    if offering.count() == 0:
        offering = get_or_create(
            session,
            Offering,
            semester=semester,
            course=course,
            section=section,
            title=title,
            units=units,
            num_seats=0,
            num_enrolled=0,
            num_reserved=0,
            num_reserved_open=0,
            num_waitlisted=0,
        )
    else:
        offering = offering.first()
        if offering.title != title:
            print(' '.join([
                f'title change in {offering.semester.code}',
                f'offering {offering.course.department.code} {offering.course.number} {offering.section}:',
                f'{offering.title} -> {title}',
            ]))
        if offering.units != int(units):
            print(' '.join([
                'units change in {offering.semester.code}',
                f'offering {offering.course.department.code} {offering.course.number} {offering.section}:',
                f'{offering.units} -> {units}',
            ]))
    offering.title = title
    offering.units = int(units)
    offering.instructors = instructors
    offering.meetings = meetings
    offering.cores = cores
    offering.num_seats = int(num_seats)
    offering.num_enrolled = int(num_enrolled)
    offering.num_reserved = int(num_reserved)
    offering.num_reserved_open = int(num_reserved_open)
    offering.num_waitlisted = int(num_waitlisted)
    return offering


def extract_text(soup):
    text = []
    for desc in soup.descendants:
        if not hasattr(desc, 'contents'):
            if desc.strip():
                text.append(desc.strip())
    return re.sub(r'  \+', ' ', ''.join(text).strip())


def get_view_state():
    response = requests.get(COURSE_COUNTS, verify=False)
    if response.status_code != 200:
        raise IOError(f'Unable to connect to Course Counts Simple Search (status code {response.status_code})')
    soup = BeautifulSoup(response.text, 'html.parser')
    view_state = soup.select('#__VIEWSTATE')[0]['value'].strip()
    event_validation = soup.select('#__EVENTVALIDATION')[0]['value'].strip()
    return view_state, event_validation


def get_offerings_data(semester):
    params = {
        'ScriptManager2':'pageUpdatePanel|tabContainer$TabPanel1$btnGo',
        '__ASYNCPOST':'true',
        '__EVENTARGUMENT':'',
        '__EVENTTARGET':'',
        '__LASTFOCUS':'',
        '__VIEWSTATEENCRYPTED':'',
        '__VIEWSTATEGENERATOR':'47F6A1AC',
        'tabContainer$TabPanel1$btnGo':'Go',
        'tabContainer$TabPanel1$ddlSemesters':semester,
        'tabContainer$TabPanel1$ddlSubjects':'',
        'tabContainer$TabPanel1$txtCrseNum':'',
        'tabContainer$TabPanel2$ddlCoreAreas':'CPFA',
        'tabContainer$TabPanel2$ddlCoreSubj':'AMST',
        'tabContainer$TabPanel2$ddlCoreTerms':semester,
        'tabContainer$TabPanel3$ddlAdvDays':'u',
        'tabContainer$TabPanel3$ddlAdvSubj':'AMST',
        'tabContainer$TabPanel3$ddlAdvTerms':semester,
        'tabContainer$TabPanel3$ddlAdvTimes':'07000755',
        'tabContainer$TabPanel4$ddlCRNTerms':semester,
        'tabContainer$TabPanel4$txtCRN':'',
        'tabContainer$TabPanel5$ddlMajorsTerm':semester,
        'tabContainer_ClientState':'{"ActiveTabIndex":0,"TabEnabledState":[true,true,true,true,true],"TabWasLoadedOnceState":[true,false,false,false,false]}',
    }
    params['__VIEWSTATE'], params['__EVENTVALIDATION'] = get_view_state()
    response = requests.post(COURSE_COUNTS, headers=REQUEST_HEADERS, data=params, verify=False)
    if response.status_code != 200:
        raise IOError(f'Unable to connect to Course Counts offerings data (status code {response.status_code})')
    response = response.text.split('|')
    if response[2] != '':
        raise ValueError('Unable to extract offerings data')
    html = []
    for data in response[7:]:
        if data.isdigit():
            break
        html.append(data)
    return '|'.join(html)


def update_from_html(session, semester, html):
    semester = Semester.code_to_season(semester)
    soup = BeautifulSoup(html, 'html.parser').find_all(id='searchResultsPanel')[0]
    soup = soup.find_all('div', recursive=False)[1].find_all('table', limit=1)[0]
    extracted_sections = set()
    for row in soup.find_all('tr', recursive=False):
        tds = row.find_all('td', recursive=False)
        if not tds:
            continue
        department_code, number, section = extract_text(tds[1]).split()
        title = extract_text(tds[2])
        units = int(extract_text(tds[3]))
        instructors = []
        for tag in tds[4].find_all('abbr'):
            instructor = tag['title']
            if instructor != 'Instructor Unassigned':
                instructors.append(instructor)
        meetings = []
        for tr in tds[5].find_all('tr'):
            # time_str, days_str
            meetings.append([extract_text(td) for td in tr.find_all('td')])
        # tds[6] is the location, which is always TBD for non-authenticated use
        cores = []
        for tag in tds[6].find_all('abbr'):
            cores.append(extract_text(tag))
        cores = [core for core in cores if core]
        num_seats = int(extract_text(tds[7]))
        num_enrolled = int(extract_text(tds[8]))
        num_reserved = int(extract_text(tds[9]))
        num_reserved_open = int(extract_text(tds[10]))
        num_waitlisted = int(extract_text(tds[11]))
        offering = create_objects(
            session, semester, department_code, number, section, title, units, instructors, meetings, cores,
            num_seats, num_enrolled, num_reserved, num_reserved_open, num_waitlisted
        )
        offering_str = f'{offering.course.department.code} {offering.course.number} {offering.section}'
        if offering_str in extracted_sections:
            print('DUPLICATE COURSE-SECTION ID: ' + offering_str)
        else:
            extracted_sections.add(offering_str)
    return extracted_sections


def get_existing_sections(session, semester_code):
    existing_sections = set()
    query = create_query(session)
    query = filter_by_semester(session, query, semester_code)
    for offering in query:
        offering_str = f'{offering.course.department.code} {offering.course.number} {offering.section}'
        existing_sections.add(offering_str)
    return existing_sections


def delete_section(session, semester_code, dept, num, sec):
    query = create_query(session)
    query = filter_by_semester(session, query, semester_code)
    query = filter_by_department(session, query, dept)
    query = filter_by_number_str(session, query, num)
    query = filter_by_section(session, query, sec)
    for offering in query:
        print(f'deleting {semester_code} offering of {dept} {num} {sec}')
        session.delete(offering)


def update_offerings(semester_code, session=None):
    DB_PATH.unlink()
    with DUMP_PATH.open(encoding='utf-8') as fd:
        old_dump = fd.read()
    create_db()
    if session is None:
        session = create_session()
    old_sections = get_existing_sections(session, semester_code)
    offerings_data = get_offerings_data(semester_code)
    new_sections = update_from_html(session, semester_code, offerings_data)
    for section_str in sorted(old_sections - new_sections):
        delete_section(session, semester_code, *section_str.split())
    session.commit()
    dump()
    with DUMP_PATH.open(encoding='utf-8') as fd:
        new_dump = fd.read()
    if old_dump != new_dump:
        with LAST_UPDATE_PATH.open('w', encoding='utf-8') as fd:
            fd.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z').strip())
            fd.write('\n')
    DB_PATH.unlink()


# audit functions


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
            print(f'Course {course} is never referenced; deleting...')
            session.delete(course)
    for department in session.query(Department).all():
        if not session.query(Course).filter(Course.department == department).first():
            print(f'Department {department} is never referenced; deleting...')
            session.delete(department)

    for offering_instructor in session.query(OfferingInstructor).all():
        if not session.query(Offering).filter(Offering.id == offering_instructor.offering_id).first():
            print(f'OfferingInstructor {offering_instructor} is never referenced; deleting...')
            session.delete(offering_instructor)
    for person in session.query(Person).all():
        if not session.query(OfferingInstructor).filter(OfferingInstructor.instructor_id == person.id).first():
            print(f'Person {person} is never referenced; deleting...')
            session.delete(person)

    for offering_core in session.query(OfferingCore).all():
        if not session.query(Offering).filter(Offering.id == offering_core.offering_id).first():
            print(f'OfferingCore {offering_core} is never referenced; deleting...')
            session.delete(offering_core)
    for core in session.query(Core).all():
        if not session.query(OfferingCore).filter(OfferingCore.core_code == core.code).first():
            print(f'Core {core} is never referenced; deleting...')
            session.delete(core)

    for offering_meeting in session.query(OfferingMeeting).all():
        if not session.query(Offering).filter(Offering.id == offering_meeting.offering_id).first():
            print(f'OfferingMeeting {offering_meeting} is never referenced; deleting...')
            session.delete(offering_meeting)
    for meeting in session.query(Meeting).all():
        if not session.query(OfferingMeeting).filter(OfferingMeeting.meeting_id == meeting.id).first():
            print(f'Meeting {meeting} is never referenced; deleting...')
            session.delete(meeting)
    for room in session.query(Room).all():
        if not session.query(Meeting).filter(Meeting.room == room).first():
            print(f'Room {room} is never referenced; deleting...')
            session.delete(room)
    for building in session.query(Building).all():
        if not session.query(Room).filter(Room.building == building).first():
            print(f'Building {building} is never referenced; deleting...')
            session.delete(building)
    for timeslot in session.query(TimeSlot).all():
        if not session.query(Meeting).filter(Meeting.timeslot == timeslot).first():
            print(f'Timeslot {timeslot} is never referenced; deleting...')
            session.delete(timeslot)

    for semester in session.query(Semester).all():
        if not session.query(Offering).filter(Offering.semester == semester).first():
            print(f'Semester {semester} is never referenced; deleting...')
            session.delete(semester)


def check_children(session):
    """Assert referenced members of all objects exist.

    Arguments:
        session (Session): The DB connection session.
    """
    for offering in session.query(Offering).all():
        semester = session.query(Semester).get(offering.semester_id)
        assert semester, f'Cannot find semester of {offering}'
        course = session.query(Course).get(offering.course_id)
        assert course, f'Cannot find course of {offering}'
        department = session.query(Department).get(course.department_code)
        assert department, f'Cannot find department of {course}'

    for offering_meeting in session.query(OfferingMeeting).all():
        offering = session.query(Offering).get(offering_meeting.offering_id)
        assert offering, f'Cannot find offering of {offering_meeting}'
        meeting = session.query(Meeting).get(offering_meeting.meeting_id)
        assert meeting, f'Cannot find meeting of {offering_meeting}'
        if meeting.timeslot_id:
            timeslot = session.query(TimeSlot).get(meeting.timeslot_id)
            assert timeslot, f'Cannot find timeslot of {meeting}'
        if meeting.room_id:
            room = session.query(Room).get(meeting.room_id)
            assert room, f'Cannot find room of {meeting}'
            building = session.query(Building).get(room.building_code)
            assert building, f'Cannot find building of {room}'

    for offering_instructor in session.query(OfferingInstructor).all():
        offering = session.query(Offering).get(offering_instructor.offering_id)
        assert offering, f'Cannot find offering of {offering_instructor}'
        instructor = session.query(Person).get(offering_instructor.instructor_id)
        assert instructor, f'Cannot find instructor of {offering_instructor}'

    for offering_core in session.query(OfferingCore).all():
        offering = session.query(Offering).get(offering_core.offering_id)
        assert offering, f'Cannot find offering of {offering_core}'
        core = session.query(Core).get(offering_core.core_code)
        assert core, f'Cannot find instructor of {offering_core}'

    for course_desc in session.query(CourseDescription).all():
        course = session.query(Course).get(course_desc.course_id)
        assert course, f'Cannot find course of {course_desc}'


def audit():
    """Remove any unused instances in the DB."""
    session = create_session()
    delete_orphans(session)
    check_children(session)
    session.commit()


# cleanup functions


def dump():

    def _dump(command, path):
        output = run(
            ['sqlite3', DB_PATH, command],
            capture_output=True,
            check=True,
        ).stdout.decode('utf-8')
        output = output.replace('PRAGMA foreign_keys=OFF;', 'PRAGMA foreign_keys=ON;')
        with path.open('w', encoding='utf-8') as fd:
            fd.write(output)

    create_db()
    _dump('.schema', SCHEMA_PATH)
    _dump('.dump', DUMP_PATH)


def main():
    chdir(ROOT_DIRECTORY)
    arg_parser = ArgumentParser()
    arg_parser.add_argument('action', choices=['audit', 'offerings', 'catalog'], help='the action to take')
    arg_parser.add_argument('arg', nargs='?', help='argument depending on the action')
    args = arg_parser.parse_args()
    if args.action == 'audit':
        audit()
    elif args.action == 'offerings':
        if args.arg:
            semester = args.arg
        else:
            semester = Semester.current_semester_code()
        update_offerings(semester)
    elif args.action == 'catalog':
        if args.arg:
            year = int(args.arg)
        else:
            year = int(Semester.current_semester_code()[:4])
        update_course_info(year)


if __name__ == '__main__':
    main()
