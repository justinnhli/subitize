#!/usr/bin/env python3

import re

from argparse import ArgumentParser

from models import OFFERINGS_FILE, Semester, Meeting, Department, Faculty, Core, Course, Offering
from subitizelib import filter_study_abroad, filter_by_search, filter_by_semester, sort_offerings

OFFERINGS = filter_study_abroad(tuple(Offering.all()))

def _extract_text(soup):
    text = []
    for desc in soup.descendants:
        if not hasattr(desc, 'contents'):
            if desc.strip():
                text.append(desc.strip())
    return re.sub(r'  \+', ' ', ''.join(text).strip())

def _request_counts(semester):
    # just-in-time import to allow non-virtualenv usage
    import requests
    url = 'https://counts.oxy.edu/'
    headers = {
        'Host':'counts.oxy.edu',
        'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:42.0) Gecko/20100101 Firefox/42.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'en-US,en;q=0.5',
        'X-Requested-With':'XMLHttpRequest',
        'X-MicrosoftAjax':'Delta=true',
        'Cache-Control':'no-cache',
        'Content-Type':'application/x-www-form-urlencoded; charset=utf-8',
        'Referer':'http://counts.oxy.edu/',
        'Connection':'keep-alive',
        'Pragma':'no-cache',
    }
    params = {
        'ScriptManager1':'pageUpdatePanel%7CtabContainer%24TabPanel3%24btnAdvGo',
        'ScriptManager1_HiddenField':'%3B%3BAjaxControlToolkit%2C%20Version%3D1.0.10920.32880%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3D28f01b0e84b6d53e%3Aen-US%3A816bbca1-959d-46fd-928f-6347d6f2c9c3%3Ae2e86ef9%3A1df13a87%3Aee0a475d%3Ac4c00916%3A9ea3f0e2%3A9e8e87e9%3A4c9865be%3Aa6a5a927%3B',
        'tabContainer%24TabPanel1%24ddlSemesters':semester,
        'tabContainer%24TabPanel1%24ddlSubjects':'',
        'tabContainer%24TabPanel1%24txtCrseNum':'',
        'tabContainer%24TabPanel2%24ddlCoreTerms':'201002',
        'tabContainer%24TabPanel2%24ddlCoreAreas':'CPFA',
        'tabContainer%24TabPanel2%24ddlCoreSubj':'AMST',
        'tabContainer%24TabPanel3%24ddlAdvTerms':semester,
        'tabContainer%24TabPanel3%24ddlAdvSubj':'',
        'tabContainer%24TabPanel3%24ddlAdvInstructors':'',
        'tabContainer%24TabPanel3%24ddlAdvTimes':'',
        'tabContainer%24TabPanel3%24ddlAdvDays':'',
        'tabContainer%24TabPanel4%24ddlCRNTerms':'201002',
        'tabContainer%24TabPanel4%24txtCRN':'',
        'tabContainer%24TabPanel3%24btnAdvGo':'Go',
        '__EVENTTARGET':'',
        '__EVENTARGUMENT':'',
        '__LASTFOCUS':'',
        '__VIEWSTATEGENERATOR':'CA0B0334',
        '__VIEWSTATEENCRYPTED':'',
        '__AjaxControlToolkitCalendarCssLoaded':'',
        'tabContainer_ClientState':'%7B%22ActiveTabIndex%22%3A2%2C%22TabState%22%3A%5Btrue%2Ctrue%2Ctrue%2Ctrue%5D%7D',
        '__ASYNCPOST':'true',
    }
    with open('viewstate.data') as fd:
        params['__VIEWSTATE'] = fd.read().strip()
    with open('eventvalidation.data') as fd:
        params['__EVENTVALIDATION'] = fd.read().strip()
    data = '&'.join('{}={}'.format(k, v) for k, v in params.items())
    return requests.post(url, headers=headers, data=data)

def _extract_results(html, year, season):
    # just-in-time import to allow non-virtualenv usage
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser').find_all(id='searchResultsPanel')[0]
    soup = soup.find_all('div', recursive=False)[1].find_all('table', limit=1)[0]
    semester = Semester(year, season)
    for row in soup.find_all('tr', recursive=False):
        tds = row.find_all('td', recursive=False)
        if not tds:
            continue
        department, number, section = _extract_text(tds[1]).split()
        course = Course(Department.get(department), number)
        title = _extract_text(tds[2])
        units = int(_extract_text(tds[3]))
        instructors = []
        for tag in tds[4].find_all('abbr'):
            instructor_str = tag['title']
            if instructor_str == 'Instructor Unassigned':
                instructors.append(None)
            else:
                instructors.append(Faculty(instructor_str, *Faculty.split_name(instructor_str)))
        meetings = []
        for tr in tds[5].find_all('tr'):
            meetings.append(Meeting.from_str(*(_extract_text(tag) for tag in tr.find_all('td'))))
        cores = list(set(Core.get(_extract_text(tag)) for tag in tds[6].find_all('abbr')))
        if not cores:
            cores = []
        seats = int(_extract_text(tds[7]))
        enrolled = int(_extract_text(tds[8]))
        reserved = int(_extract_text(tds[9]))
        reserved_open = int(_extract_text(tds[10]))
        waitlisted = int(_extract_text(tds[11]))
        Offering(semester, course, section, title, units, tuple(instructors), tuple(meetings), tuple(cores), seats, enrolled, reserved, reserved_open, waitlisted)

def get_data_from_web(semester):
    response = _request_counts(semester.code).text.split('|')
    if response[2] != '':
        print('Request to Course Counts resulted in status code {}; quitting.'.format(response[2]))
        exit(1)
    with open('response', 'w') as fd:
        fd.write(response[7])
    _extract_results(response[7], semester.year, semester.season)

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

def update_db(semester):
    get_data_from_web(semester)
    with open(OFFERINGS_FILE, 'w') as fd:
        fd.write('\t'.join(HEADINGS) + '\n')
        offerings = Offering.all()
        offerings = sorted(offerings, key=(lambda offering: (int(offering.semester.code), offering.course, offering.section)))
        for offering in offerings:
            if offering.instructors == (None,): # TODO this is stupid
                instructor_str = 'Instructor Unassigned'
            else:
                instructor_str = '; '.join(repr(instructor) for instructor in sorted(offering.instructors, key=(lambda instructor: instructor.last_name)))
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
    arg_parser.add_argument('--update', action='store_true', default=False)
    args = arg_parser.parse_args()
    if args.semester == 'any':
        offerings = OFFERINGS
    else:
        semester = Semester.from_code(args.semester)
        offerings = filter_by_semester(OFFERINGS, semester.code)
    if args.update:
        if args.semester == 'any':
            arg_parser.error('Must specify single --semester in conjunction with --update')
        update_db(semester)
    else:
        search(offerings, ' '.join(args.terms), sort=args.sort)

if __name__ == '__main__':
    main()
