#!/usr/bin/env python3

import re
from datetime import datetime
from math import ceil
from collections import namedtuple

from flask import Flask, render_template, request, url_for

from subitize import to_semester, to_year_season, get_data_from_file
from subitize import DEPARTMENT_ABBRS, CORE_ABBRS

INSTRUCTOR_PREFERRED_NAMES = {
    'Ning Hui Li': 'Justin Li',
    'William Dylan Sabo': 'Dylan Sabo',
    'Aleksandra Sherman': 'Sasha Sherman',
    'Charles Potts': 'Brady Potts',
    'Amanda J. Zellmer McCormack': 'Amanda J. Zellmer',
}

INSTRUCTOR_LAST_NAMES = {
    'Allison de Fren': 'de Fren',
}

def get_current_year_season():
    today = datetime.now()
    if today.month < 3 or (today.month == 3 and today.day < 15):
        year = today.year
        season = 'spring'
    elif (today.month == 3 and today.day >= 15) or 4 <= today.month < 11:
        year = str(today.year)
        season = 'fall'
    else:
        year = str(today.year + 1)
        season = 'spring'
    return year, season

def get_course_number(number):
    return int(re.sub('[^0-9]', '', number))

def get_first_last_names(instructor):
    if instructor in INSTRUCTOR_LAST_NAMES:
        last_name = INSTRUCTOR_LAST_NAMES[instructor]
        first_name = instructor[:len(instructor) - len(last_name) - 1]
    else:
        if instructor in INSTRUCTOR_PREFERRED_NAMES:
            instructor = INSTRUCTOR_PREFERRED_NAMES[instructor]
        first_name, last_name = instructor.rsplit(' ', maxsplit=1)
    return (first_name, last_name)

Result = namedtuple('Result', ('offering', 'semester', 'course', 'title', 'units', 'instructors', 'meetings', 'core'))

def to_result(offering):
    semester = offering.year + ' ' + offering.season.capitalize()
    course = ' '.join([offering.department, offering.number, offering.section])
    title = offering.title
    units = offering.units
    instructors = []
    for instructor in offering.instructors:
        first_name, last_name = get_first_last_names(instructor)
        instructors.append((last_name, first_name + ' ' + last_name))
    instructors = sorted(instructors)
    meetings = []
    for meeting in offering.meetings:
        if meeting.start_time is None:
            meetings.append('TBD')
            break
        else:
            result = ''
            result += meeting.start_time.strftime('%I:%M%p')
            result += '-'
            result += meeting.end_time.strftime('%I:%M%p')
            result += ' '
            result = result.lower()
            result += meeting.days
            result += ' ('
            if meeting.location is None:
                result += 'TBD'
            else:
                result += meeting.location
            result += ')'
            meetings.append(result)
    meetings = '; '.join(meetings)
    core = []
    for code in offering.core:
        core.append((code, CORE_ABBRS[code]))
    core = sorted(core)
    return Result(offering, semester, course, title, units, instructors, meetings, core)

app = Flask(__name__)

@app.route("/")
def view_root():
    offerings = get_data_from_file()
    offerings = tuple(o for o in offerings if not (o.department == 'OXAB' or o.department.startswith('AB')))
    parameters = request.args.to_dict()
    context = {}
    # get search results, if necessary
    if len(parameters) == 0:
        results = []
        semester = to_semester(*get_current_year_season())
    else:
        results = offerings
        if 'query' in parameters and parameters.get('query') != 'search for courses...':
            terms = parameters.get('query').lower().split()
            results = []
            for offering in offerings:
                match = True
                for term in terms:
                    if any(term in instructor.lower() for instructor in offering.instructors):
                        continue
                    if term in offering.title.lower():
                        continue
                    match = False
                    break
                if match:
                    results.append(offering)
            context['form_query'] = parameters.get('query')
        if 'semester' in parameters and parameters.get('semester') == '':
            semester = ''
        else:
            if 'semester' in parameters:
                year, season = to_year_season(parameters.get('semester'))
            else:
                year, season = get_current_year_season()
            semester = to_semester(year, season)
            results = tuple(offering for offering in results if offering.year == year and offering.season == season)
        if 'department' in parameters and parameters.get('department') != '':
            results = tuple(offering for offering in results if offering.department == parameters.get('department'))
        results = tuple(offering for offering in results if get_course_number(offering.number) >= int(parameters.get('lower')))
        results = tuple(offering for offering in results if get_course_number(offering.number) <= int(parameters.get('upper')))
        if 'units' in parameters and parameters.get('units') != '':
            results = tuple(offering for offering in results if offering.units == parameters.get('units'))
        if 'instructor' in parameters and parameters.get('instructor') != '':
            results = tuple(offering for offering in results if parameters.get('instructor') in offering.instructors)
        if 'core' in parameters and parameters.get('core') != '':
            results = tuple(offering for offering in results if parameters.get('core') in offering.core)
    context['searching'] = (len(parameters) > 0)
    context['results'] = tuple(to_result(o) for o in results)
    # sort search results
    if 'sort' in parameters:
        field = parameters.pop('sort')
        if field in ('course', 'title', 'units', 'instructors', 'core'):
            context['results'] = sorted(context['results'], key=(lambda result: getattr(result, field)))
        elif field == 'semester':
            context['results'] = sorted(context['results'], key=(lambda result: result.offering.semester))
        elif field == 'meetings':
            context['results'] = sorted(context['results'], key=(lambda result: sorted(result.offering.meetings)))
    # get dropdown options
    context['semesters'] = set()
    context['departments'] = set()
    context['upper'] = set()
    context['units'] = set()
    context['cores'] = set()
    context['instructors'] = set()
    for o in offerings:
        offering_semester = to_semester(o.year, o.season)
        context['semesters'].add((offering_semester, o.year + ' ' + o.season.capitalize(), offering_semester == semester))
        context['departments'].add((o.department, DEPARTMENT_ABBRS[o.department], o.department == parameters.get('department')))
        context['upper'].add(ceil(get_course_number(o.number) / 100) * 100 - 1)
        context['units'].add((o.units, o.units == parameters.get('units')))
        context['cores'].update((core, CORE_ABBRS[core], core == parameters.get('core')) for core in o.core if core != '')
        for instructor in o.instructors:
            instructor_id = instructor
            first_name, last_name = get_first_last_names(instructor)
            display_name = '{}, {}'.format(last_name, first_name)
            context['instructors'].add((instructor_id, display_name, instructor_id == parameters.get('instructor')))
    context['semesters'] = sorted(context['semesters'], reverse=True)
    context['departments'] = sorted(context['departments'])
    if 'lower' in parameters and parameters.get('lower') != '':
        context['lower'] = parameters.get('lower')
    else:
        context['lower'] = 0
    if 'upper' in parameters and parameters.get('upper') != '':
        context['upper'] = parameters.get('upper')
    else:
        context['upper'] = max(context['upper'])
    context['units'] = sorted(context['units'])
    context['cores'] = sorted(context['cores'], key=(lambda l: l[1]))
    context['instructors'] = sorted(context['instructors'], key=(lambda seq: seq[1].lower()))
    context['url'] = url_for('view_root', **parameters)
    return render_template('base.html', **context)

if __name__ == "__main__":
    app.run(debug=True)
