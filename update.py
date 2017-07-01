#!/usr/bin/env python3

import re
from argparse import ArgumentParser
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import create_session, get_or_create
from models import Semester, TimeSlot, Building, Room, Meeting, Core, Department, Course, Person, Offering

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

def extract_text(soup):
    text = []
    for desc in soup.descendants:
        if not hasattr(desc, 'contents'):
            if desc.strip():
                text.append(desc.strip())
    return re.sub(r'  \+', ' ', ''.join(text).strip())

def get_view_state():
    response = requests.get(COURSE_COUNTS)
    assert response.status_code == 200, 'Unable to connect to Course Counts Simple Search (status code {})'.format(response.status_code)
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
    assert response.status_code == 200, 'Unable to connect to Course Counts offerings data (status code {})'.format(response.status_code)
    response = response.text.split('|')
    assert response[2] == '', 'Unable to extract offerings data'
    return response[7]

def extract_instructors(session, td):
    instructors = []
    for tag in td.find_all('abbr'):
        instructor_str = tag['title']
        if instructor_str != 'Instructor Unassigned':
            first_name, last_name = instructor_str.rsplit(' ', maxsplit=1)
            instructor = get_or_create(session, Person, system_name=instructor_str, first_name=first_name, last_name=last_name)
            instructors.append(instructor)
    return instructors

def extract_room(session, location_str):
    if location_str == 'Bldg-TBD':
        room = None
    elif len(location_str.split()) == 1 and location_str in ('AGYM', 'KECK', 'UEPI', 'MULLIN', 'BIRD', 'TENNIS', 'THORNE', 'FM', 'CULLEY', 'TREE', 'RUSH', 'LIB', 'HERR'):
        building = get_or_create(session, Building, code=location_str)
        room = get_or_create(session, Room, building=building, room=None)
    else:
        building_str, room_str = location_str.rsplit(' ', maxsplit=1)
        building = get_or_create(session, Building, code=building_str)
        room = get_or_create(session, Room, building=building, room=room_str)
    return room

def extract_meetings(session, td):
    meetings = []
    for tr in td.find_all('tr'):
        time_str, days_str, location_str = ((extract_text(td) for td in tr.find_all('td')))
        if time_str == 'Time-TBD' or days_str == 'Days-TBD':
            timeslot = None
            room = None
        else:
            start_time_str, end_time_str = time_str.upper().split('-')
            start_time = datetime.strptime(start_time_str, '%I:%M%p').time()
            end_time = datetime.strptime(end_time_str, '%I:%M%p').time()
            timeslot = get_or_create(session, TimeSlot, weekdays=days_str, start=start_time, end=end_time)
            room = extract_room(session, location_str)
        if timeslot is not None:
            meeting = get_or_create(session, Meeting, timeslot=timeslot, room=room)
            meetings.append(meeting)
    return meetings

def extract_cores(session, td):
    cores = []
    for tag in td.find_all('abbr'):
        core = get_or_create(session, Core, code=extract_text(tag))
        cores.append(core)
    return cores

def extract_results(session, semester, html):
    soup = BeautifulSoup(html, 'html.parser').find_all(id='searchResultsPanel')[0]
    soup = soup.find_all('div', recursive=False)[1].find_all('table', limit=1)[0]
    for row in soup.find_all('tr', recursive=False):
        tds = row.find_all('td', recursive=False)
        if not tds:
            continue
        department_code, number, section = extract_text(tds[1]).split()
        department = get_or_create(session, Department, code=department_code)
        course = get_or_create(session, Course, department=department, number=number, number_int=int(re.sub('[^0-9]', '', number)))
        title = extract_text(tds[2])
        units = int(extract_text(tds[3]))
        instructors = extract_instructors(session, tds[4])
        meetings = extract_meetings(session, tds[5])
        cores = extract_cores(session, tds[6])
        num_seats = int(extract_text(tds[7]))
        num_enrolled = int(extract_text(tds[8]))
        num_reserved = int(extract_text(tds[9]))
        num_reserved_open = int(extract_text(tds[10]))
        num_waitlisted = int(extract_text(tds[11]))
        offering = get_or_create(
            session,
            Offering,
            semester=semester,
            course=course,
            section=section,
            title=title,
            units=units,
            num_seats=num_seats,
            num_enrolled=num_enrolled,
            num_reserved=num_reserved,
            num_reserved_open=num_reserved_open,
            num_waitlisted=num_waitlisted,
        )
        offering.instructors.extend(instructors)
        offering.meetings.extend(meetings)
        offering.cores.extend(cores)

def update_db(semester_code, session=None):
    if session is None:
        session = create_session()
    year, season = Semester.code_to_season(semester_code)
    semester = get_or_create(session, Semester, year=year, season=season)
    session.query(Offering).filter_by(semester_id=semester.id).delete()
    offerings_data = get_offerings_data(semester_code)
    extract_results(session, semester, offerings_data)
    session.commit()

def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument('semester', nargs='?', default=Semester.current_semester().code)
    arg_parser.add_argument('--raw', action='store_true')
    args = arg_parser.parse_args()
    if args.raw:
        print(get_offerings_data(args.semester))
    else:
        update_db(args.semester)

if __name__ == '__main__':
    main()
