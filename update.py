#!/usr/bin/env python3

import re
from argparse import ArgumentParser

import requests
from bs4 import BeautifulSoup

from models import OFFERINGS_FILE, Semester, Meeting, Department, Faculty, Core, Course, Offering

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

def extract_results(html, year, season):
    soup = BeautifulSoup(html, 'html.parser').find_all(id='searchResultsPanel')[0]
    soup = soup.find_all('div', recursive=False)[1].find_all('table', limit=1)[0]
    semester = Semester(year, season)
    for row in soup.find_all('tr', recursive=False):
        tds = row.find_all('td', recursive=False)
        if not tds:
            continue
        department, number, section = extract_text(tds[1]).split()
        course = Course(Department.get(department), number)
        title = extract_text(tds[2])
        units = int(extract_text(tds[3]))
        instructors = []
        for tag in tds[4].find_all('abbr'):
            instructor_str = tag['title']
            if instructor_str == 'Instructor Unassigned':
                instructors.append(None)
            else:
                instructors.append(Faculty(instructor_str, *Faculty.split_name(instructor_str)))
        meetings = []
        for tr in tds[5].find_all('tr'):
            meetings.append(Meeting.from_str(*(extract_text(tag) for tag in tr.find_all('td'))))
        cores = list(set(Core.get(extract_text(tag)) for tag in tds[6].find_all('abbr')))
        if not cores:
            cores = []
        seats = int(extract_text(tds[7]))
        enrolled = int(extract_text(tds[8]))
        reserved = int(extract_text(tds[9]))
        reserved_open = int(extract_text(tds[10]))
        waitlisted = int(extract_text(tds[11]))
        Offering(semester, course, section, title, units, tuple(instructors), tuple(meetings), tuple(cores), seats, enrolled, reserved, reserved_open, waitlisted)

def get_data_from_web(semester):
    offerings_data = get_offerings_data(semester.code)
    extract_results(offerings_data, semester.year, semester.season)
    return offerings_data

def update_db(semester):
    offerings_data = get_data_from_web(semester)
    with open(OFFERINGS_FILE, 'w') as fd:
        fd.write('\t'.join(HEADINGS) + '\n')
        offerings = Offering.all()
        offerings = sorted(offerings, key=(lambda offering: (int(offering.semester.code), offering.course, offering.section)))
        for offering in offerings:
            instructor_strs = []
            for instructor in offering.instructors:
                if instructor is not None:
                    instructor_strs.append((instructor.last_name, repr(instructor)))
            instructor_strs = list(pair[1] for pair in sorted(instructor_strs)) + offering.instructors.count(None) * ['Instructor Unassigned']
            instructor_str = '; '.join(instructor_strs)
            fd.write('\t'.join(str(field) for field in (
                offering.year,
                offering.season.lower(),
                offering.department.code,
                offering.number,
                offering.section,
                offering.name,
                offering.units,
                instructor_str,
                '; '.join(repr(meeting) for meeting in sorted(offering.meetings)),
                '; '.join(sorted(core.code for core in offering.cores)),
                offering.num_seats,
                offering.num_enrolled,
                offering.num_reserved,
                offering.num_reserved_open,
                offering.num_waitlisted,
            )) + '\n')
    return offerings_data

def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument('semester', nargs='?', default=Semester.current_semester().code)
    arg_parser.add_argument('--raw', default=False, action='store_true')
    args = arg_parser.parse_args()
    offerings_data = update_db(Semester.from_code(args.semester))
    if args.raw:
        with open('response', 'w') as fd:
            fd.write(offerings_data)

if __name__ == '__main__':
    main()
