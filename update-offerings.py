#!/usr/bin/env python3

import re
from argparse import ArgumentParser
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from models import create_session, get_or_create
from models import Semester, TimeSlot, Building, Room, Meeting, Core, Department, Course, Person, Offering
from subitizelib import filter_by_semester, filter_by_department, filter_by_number_str, filter_by_section

COURSE_COUNTS = 'https://counts.oxy.edu/'

HEADINGS = (
    'year',
    'season',
    'department',
    'number',
    'section',
    'title',
    'units',
    'instructors',
    'meetings',
    'cores',
    'seats',
    'enrolled',
    'reserved',
    'reserved_open',
    'waitlisted'
)

REQUEST_HEADERS = {
    'Host':'counts.oxy.edu',
    'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:42.0) Gecko/20100101 Firefox/42.0',
    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language':'en-US,en;q=0.5',
    'X-Requested-With':'XMLHttpRequest',
    'X-MicrosoftAjax':'Delta=true',
    'Cache-Control':'no-cache',
    'Content-Type':'application/x-www-form-urlencoded; charset=utf-8',
    'Referer':'https://counts.oxy.edu/',
    'Connection':'keep-alive',
    'Pragma':'no-cache',
}

MAPPED_NAMES = {
    'To the Estate of Deborah Martinson':'Deborah Martinson',
    'Carey Sargent':'Jacob Sargent',
}

PREFERRED_NAMES = {
    'Allison de Fren': {'first_name':'Allison', 'last_name':'de Fren'},
    'Amanda J. Zellmer McCormack': {'first_name':'Amanda J.', 'last_name':'Zellmer'},
}


def create_instructor(session, system_name):
    system_name = system_name.strip()
    if system_name == 'Instructor Unassigned':
        return None
    if system_name in MAPPED_NAMES:
        system_name = MAPPED_NAMES[system_name]
    first_name, last_name = system_name.rsplit(' ', maxsplit=1)
    if system_name in PREFERRED_NAMES:
        first_name = PREFERRED_NAMES.get('first_name', first_name)
        last_name = PREFERRED_NAMES.get('last_name', last_name)
    instructor = session.query(Person).filter_by(system_name=system_name)
    if instructor.count() == 0:
        return get_or_create(session, Person, system_name=system_name, first_name=first_name, last_name=last_name)
    elif instructor.count() == 1:
        return instructor.first()
    assert False


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
        session,
        semester,
        department_code,
        number,
        section,
        title,
        units,
        instructors,
        meetings,
        cores,
        num_seats,
        num_enrolled,
        num_reserved,
        num_reserved_open,
        num_waitlisted):
    semester = get_or_create(session, Semester, year=semester[0], season=semester[1])
    department = get_or_create(session, Department, code=department_code)
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
            print('title change in {} offering {} {} {}: {} -> {}'.format(
                offering.semester.code,
                offering.course.department.code, offering.course.number, offering.section,
                offering.title, title
            ))
        if offering.units != int(units):
            print('units change in {} offering {} {} {}: {} -> {}'.format(
                offering.semester.code,
                offering.course.department.code, offering.course.number, offering.section,
                offering.units, units
            ))
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
    response = requests.get(COURSE_COUNTS)
    if response.status_code != 200:
        raise IOError('Unable to connect to Course Counts Simple Search (status code {})'.format(response.status_code))
    soup = BeautifulSoup(response.text, 'html.parser')
    view_state = soup.select('#__VIEWSTATE')[0]['value'].strip()
    event_validation = soup.select('#__EVENTVALIDATION')[0]['value'].strip()
    return view_state, event_validation


def get_offerings_data(semester):
    params = {
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
        'tabContainer$TabPanel3$ddlAdvTimes':'07000755',
        'tabContainer$TabPanel4$ddlCRNTerms':semester,
        'tabContainer$TabPanel4$txtCRN':'',
        'tabContainer_ClientState':'{"ActiveTabIndex":0,"TabState":[true,true,true,true]}',
        'ScriptManager1':'pageUpdatePanel|tabContainer$TabPanel1$btnGo',
        'ScriptManager1_HiddenField':';;AjaxControlToolkit, Version=1.0.10920.32880, Culture=neutral, PublicKeyToken=28f01b0e84b6d53e:en-US:816bbca1-959d-46fd-928f-6347d6f2c9c3:e2e86ef9:1df13a87:ee0a475d:c4c00916:9ea3f0e2:9e8e87e9:4c9865be:a6a5a927;',
        '__ASYNCPOST':'true',
        '__AjaxControlToolkitCalendarCssLoaded':'',
        '__EVENTARGUMENT':'',
        '__EVENTTARGET':'',
        '__LASTFOCUS':'',
        '__VIEWSTATEENCRYPTED':'',
        '__VIEWSTATEGENERATOR':'CA0B0334',
    }
    params['__VIEWSTATE'], params['__EVENTVALIDATION'] = get_view_state()
    response = requests.post(COURSE_COUNTS, headers=REQUEST_HEADERS, data=params)
    if response.status_code != 200:
        raise IOError('Unable to connect to Course Counts offerings data (status code {})'.format(response.status_code))
    response = response.text.split('|')
    if response[2] != '':
        raise ValueError('Unable to extract offerings data')
    return response[7]


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
            # time_str, days_str, location_str
            meetings.append([extract_text(td) for td in tr.find_all('td')])
        cores = []
        for tag in tds[6].find_all('abbr'):
            cores.append(extract_text(tag))
        cores = [core for core in cores if core]
        num_seats = int(extract_text(tds[7]))
        num_enrolled = int(extract_text(tds[8]))
        num_reserved = int(extract_text(tds[9]))
        num_reserved_open = int(extract_text(tds[10]))
        num_waitlisted = int(extract_text(tds[11]))
        offering = create_objects(session, semester, department_code, number, section, title, units, instructors, meetings, cores, num_seats, num_enrolled, num_reserved, num_reserved_open, num_waitlisted)
        offering_str = '{} {} {}'.format(offering.course.department.code, offering.course.number, offering.section)
        assert offering_str not in extracted_sections
        extracted_sections.add(offering_str)
    return extracted_sections


def get_existing_sections(session, semester_code):
    existing_sections = set()
    query = session.query(Offering)
    query = query.join(Semester)
    query = query.join(Course, Department)
    query = filter_by_semester(query, semester_code)
    for offering in query:
        offering_str = '{} {} {}'.format(offering.course.department.code, offering.course.number, offering.section)
        existing_sections.add(offering_str)
    return existing_sections


def delete_section(session, semester_code, dept, num, sec):
    query = session.query(Offering)
    query = query.join(Semester)
    query = query.join(Course, Department)
    query = filter_by_semester(query, semester_code)
    query = filter_by_department(query, dept)
    query = filter_by_number_str(query, num)
    query = filter_by_section(query, sec)
    for offering in query:
        print('deleting {} offering of {} {} {}'.format(semester_code, dept, num, sec))
        session.delete(offering)


def update_db(semester_code, session=None):
    if session is None:
        session = create_session()
    old_sections = get_existing_sections(session, semester_code)
    offerings_data = get_offerings_data(semester_code)
    new_sections = update_from_html(session, semester_code, offerings_data)
    for section_str in sorted(old_sections - new_sections):
        delete_section(session, semester_code, *section_str.split())
    session.commit()


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument('semester', nargs='?', default=Semester.current_semester_code())
    arg_parser.add_argument('--raw', action='store_true')
    args = arg_parser.parse_args()
    if args.raw:
        print(get_offerings_data(args.semester))
    else:
        update_db(args.semester)


if __name__ == '__main__':
    main()
