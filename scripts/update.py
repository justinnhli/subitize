#!/usr/bin/env python3

import re
import sys
from argparse import ArgumentParser
from datetime import datetime
from os import chdir
from pathlib import Path
from random import random
from subprocess import run
from time import sleep
from urllib.parse import urlsplit, urljoin

import requests
from bs4 import BeautifulSoup, Comment
from sqlalchemy import select

ROOT_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIRECTORY))

from subitize import create_db, create_session, get_or_create
from subitize import Semester, TimeSlot, Building, Room, Meeting
from subitize import Core, Department, Course, Person
from subitize import OfferingMeeting, OfferingCore, OfferingInstructor, Offering
from subitize import CourseDescription
from subitize import create_select, filter_by_semester, filter_by_department, filter_by_number_str, filter_by_section

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
            for course_link_soup in dept_courses_soup.select('#main > ul li a'):
                course_url = urljoin(CATALOG_URL, course_link_soup['href'])
                if course_url in visited_urls:
                    continue
                if not re.match('[A-Z]+ [0-9]+', extract_text(course_link_soup)):
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
    description = str(clean_soup(course_soup.select('div.desc')[0]))
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
        #course_desc.parsed_prerequisites = parsed_prerequisites
        # TODO detect if prerequisites have changed


def update_course_info(year):
    year_cache_path = CATALOG_CACHE_PATH / str(year)
    # download all urls
    cached_files = set()
    for course_url in get_courses_urls(year):
        cache_path = (year_cache_path / urlsplit(course_url).path[1:].lower()).with_suffix('.html')
        cached_files.add(cache_path)
        if cache_path.exists() and cache_path.stat().st_size > 1000:
            continue
        print(f'downloading {course_url}...')
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open('w', encoding='utf-8') as fd:
            fd.write(get_url(course_url))
            fd.write('\n')
        sleep(random())
    # scape and save into DB
    session = create_session()
    for path in sorted(cached_files):
        course_url = urljoin(CATALOG_URL, '/' + str(path.relative_to(year_cache_path).with_suffix('')))
        print(f'parsing {course_url}...')
        with path.open(encoding='utf-8') as fd:
            extract_course_info(session, year, course_url, fd.read())
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
        print(f'adding {offering}: {offering.title} -> {title}')
    else:
        offering = offering.first()
        if offering.title != title:
            print(f'changing title of {offering}: {offering.title} -> {title}')
        if set(offering.instructors) != set(instructors):
            if offering.instructors:
                old_instructors = ', '.join(sorted(str(instructor) for instructor in offering.instructors))
            else:
                old_instructors = '(none)'
            new_instructors = ', '.join(sorted(str(instructor) for instructor in instructors))
            print(f'changing instructors of {offering}: {old_instructors} -> {new_instructors}')
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
        'tabContainer$TabPanel3$ddlAdvDays':'m',
        'tabContainer$TabPanel3$ddlAdvSubj':'AMST',
        'tabContainer$TabPanel3$ddlAdvTerms':semester,
        'tabContainer$TabPanel3$ddlAdvTimes':'08000855',
        'tabContainer$TabPanel4$ddlCRNTerms':semester,
        'tabContainer$TabPanel4$txtCRN':'',
        'tabContainer_ClientState':'{"ActiveTabIndex":0,"TabEnabledState":[true,true,true,true],"TabWasLoadedOnceState":[true,false,false,false]}',
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
    return set(
        f'{offering.course.department.code} {offering.course.number} {offering.section}'
        for offering in session.scalars(filter_by_semester(create_select(), semester_code))
    )


def delete_section(session, semester_code, dept, num, sec):
    statement = create_select()
    statement = filter_by_semester(statement, semester_code)
    statement = filter_by_department(statement, dept)
    statement = filter_by_number_str(statement, num)
    statement = filter_by_section(statement, sec)
    for offering in session.scalars(statement):
        print(f'deleting {offering}: {offering.title}')
        session.delete(offering)


def update_offerings(semester_code, session=None):
    with DUMP_PATH.open(encoding='utf-8') as fd:
        old_dump = fd.read()
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


# audit functions


def delete_orphans(session):
    """Delete unreferenced objects.

    Arguments:
        session (Session): The DB connection session.
    """
    # pylint: disable=too-many-branches, too-many-statements

    # delete courses that have never been offered
    statement = select(Course).where(~(
        select(Offering).where(Offering.course_id == Course.id).exists()
    ))
    for course in session.scalars(statement):
        print(f'Course {course} is never referenced; deleting...')
        session.delete(course)
    # delete departments that do not have courses
    statement = select(Department).where(~(
        select(Course).where(Course.department_code == Department.code).exists()
    ))
    for department in session.scalars(statement):
        print(f'Department {department} is never referenced; deleting...')
        session.delete(department)
    # delete people that do not have offerings
    statement = select(OfferingInstructor).where(~(
        select(Offering).where(Offering.id == OfferingInstructor.offering_id).exists()
    ))
    for offering_instructor in session.scalars(statement):
        print(f'OfferingInstructor {offering_instructor} is never referenced; deleting...')
        session.delete(offering_instructor)
    statement = select(Person).where(~(
        select(OfferingInstructor).where(OfferingInstructor.instructor_id == Person.id).exists()
    ))
    for person in session.scalars(statement):
        print(f'Person {person} is never referenced; deleting...')
        session.delete(person)
    # delete core requirements that do not have offerings
    statement = select(OfferingCore).where(~(
        select(Offering).where(Offering.id == OfferingCore.offering_id).exists()
    ))
    for offering_core in session.scalars(statement):
        print(f'OfferingCore {offering_core} is never referenced; deleting...')
        session.delete(offering_core)
    statement = select(Core).where(~(
        select(OfferingCore).where(OfferingCore.core_code == Core.code).exists()
    ))
    for core in session.scalars(statement):
        print(f'Core {core} is never referenced; deleting...')
        session.delete(core)
    # delete meetings that do not have offerings
    statement = select(OfferingMeeting).where(~(
        select(Offering)
        .where(Offering.id == OfferingMeeting.offering_id)
        .exists()
    ))
    for offering_meeting in session.scalars(statement):
        print(f'OfferingMeeting {offering_meeting} is never referenced; deleting...')
        session.delete(offering_meeting)
    statement = select(Meeting).where(~(
        select(OfferingMeeting).where(OfferingMeeting.meeting_id == Meeting.id).exists()
    ))
    for meeting in session.scalars(statement):
        print(f'Meeting {meeting} is never referenced; deleting...')
        session.delete(meeting)
    # delete rooms and buildings that do not have meetings
    statement = select(Room).where(~(
        select(Meeting).where(Meeting.room_id == Room.id).exists()
    ))
    for room in session.scalars(statement):
        print(f'Room {room} is never referenced; deleting...')
        session.delete(room)
    statement = select(Building).where(~(
        select(Room).where(Room.building_code == Building.code).exists()
    ))
    for building in session.scalars(statement):
        print(f'Building {building} is never referenced; deleting...')
        session.delete(building)
    # delete timeslots that do not have meetings
    statement = select(TimeSlot).where(~(
        select(Meeting).where(Meeting.timeslot_id == TimeSlot.id).exists()
    ))
    for timeslot in session.scalars(statement):
        print(f'TimeSlot {timeslot} is never referenced; deleting...')
        session.delete(timeslot)
    # delete semesters that do not have offerings
    statement = select(Semester).where(~(
        select(Offering).where(Offering.semester_id == Semester.id).exists()
    ))
    for semester in session.scalars(statement):
        print(f'Semester {semester} is never referenced; deleting...')
        session.delete(semester)


def audit():
    """Remove any unused instances in the DB."""
    session = create_session()
    delete_orphans(session)
    session.commit()
    dump()


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
    DB_PATH.unlink()
    create_db()
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
    DB_PATH.unlink()


if __name__ == '__main__':
    main()
