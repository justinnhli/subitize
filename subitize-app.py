#!/usr/bin/env python3

from datetime import datetime
from math import ceil
from collections import namedtuple

from flask import Flask, render_template, request, url_for

from subitizelib import CORE_ABBRS, DEPARTMENT_ABBRS
from subitizelib import Meeting
from subitizelib import get_data_from_file, to_semester, get_current_year_season
from subitizelib import filter_study_abroad, filter_by_search, filter_by_semester, filter_by_department, filter_by_number, filter_by_units, filter_by_instructor, filter_by_core

OFFERINGS = tuple(get_data_from_file())

OPTIONS_SEMESTERS = sorted(set((to_semester(o.year, o.season), o.year + ' ' + o.season.capitalize()) for o in OFFERINGS), reverse=True)
OPTIONS_INSTRUCTORS = sorted(set((instructor, instructor.display_name) for o in OFFERINGS for instructor in o.instructors), key=(lambda seq: seq[1].lower()))
OPTIONS_CORES = sorted(set((core, CORE_ABBRS[core]) for o in OFFERINGS for core in o.cores))
OPTIONS_UNITS = sorted(set(o.units for o in OFFERINGS))
OPTIONS_DEPARTMENTS = sorted(set((o.department, DEPARTMENT_ABBRS[o.department]) for o in OFFERINGS))
OPTIONS_LOWER = 0
OPTIONS_UPPER = max(ceil(o.number_as_int / 100) * 100 - 1 for o in OFFERINGS)
OPTIONS_DAYS = [(code, Meeting.WEEKDAY_ABBRS[code]) for code in Meeting.WEEKDAYS]
OPTIONS_HOURS = [(str(hour), hour) for hour in (12, *range(1, 12))]
OPTIONS_MERIDIANS = ['am', 'pm']

def get_parameter(parameters, parameter, default=''):
    value = parameters.get(parameter)
    if value != default:
        return value
    else:
        return None

def get_search_results(parameters, context):
    if len(parameters) == 0:
        context['results'] = None
    else:
        results = filter_study_abroad(OFFERINGS)
        results = filter_by_search(results, get_parameter(parameters, 'query', default='search for courses...'))
        results = filter_by_semester(results, get_parameter(parameters, 'semester'))
        results = filter_by_department(results, get_parameter(parameters, 'department'))
        results = filter_by_number(results, int(get_parameter(parameters, 'lower')), int(get_parameter(parameters, 'upper')))
        results = filter_by_units(results, get_parameter(parameters, 'units'))
        results = filter_by_instructor(results, get_parameter(parameters, 'instructor'))
        results = filter_by_core(results, get_parameter(parameters, 'core'))
        if get_parameter(parameters, 'day'):
            results = tuple(offering for offering in results if any(meeting.days is None or (parameters.get('day') in meeting.days) for meeting in offering.meetings))
        start_hour = datetime.strptime(parameters.get('start_hour') + parameters.get('start_meridian'), '%I%p').time()
        results = tuple(offering for offering in results if all((meeting.start_time is None or start_hour < meeting.start_time) for meeting in offering.meetings))
        end_hour = datetime.strptime(parameters.get('end_hour') + parameters.get('end_meridian'), '%I%p').time()
        results = tuple(offering for offering in results if all((meeting.end_time is None or meeting.end_time < end_hour) for meeting in offering.meetings))
        context['results'] = tuple(to_result(o) for o in results)
        context['query'] = parameters.get('query')
    return context

def sort_search_results(parameters, context):
    if 'sort' in parameters:
        field = parameters.get('sort')
        if field == 'semester':
            context['results'] = sorted(context['results'], key=(lambda result: result.offering.semester))
        elif field == 'meetings':
            context['results'] = sorted(context['results'], key=(lambda result: sorted(result.offering.meetings)))
        else:
            context['results'] = sorted(context['results'], key=(lambda result: getattr(result, field)))
    return context

def get_dropdown_options(parameters, context, semester):
    context['semesters'] = tuple((code, o_semester, code == semester) for code, o_semester in OPTIONS_SEMESTERS)
    context['instructors'] = tuple((code, instructor, instructor == parameters.get('instructor')) for code, instructor in OPTIONS_INSTRUCTORS)
    context['cores'] = tuple((code, core, code == parameters.get('core')) for code, core in OPTIONS_CORES)
    context['units'] = tuple((unit, unit == parameters.get('units')) for unit in OPTIONS_UNITS)
    context['departments'] = tuple((code, department, code == parameters.get('department')) for code, department in OPTIONS_DEPARTMENTS)
    context['lower'] = (OPTIONS_LOWER if parameters.get('lower') is None else parameters.get('lower'))
    context['upper'] = (OPTIONS_UPPER if parameters.get('upper') is None else parameters.get('upper'))
    context['days'] = tuple((code, day, code == parameters.get('day')) for code, day in OPTIONS_DAYS)
    context['start_hours'] = tuple((value, hour, value == parameters.get('start_hour')) for value, hour in OPTIONS_HOURS)
    context['start_meridians'] = tuple((meridian, meridian == parameters.get('start_meridian')) for meridian in OPTIONS_MERIDIANS)
    if len(parameters) == 0:
        parameters['end_hour'] = '11'
        parameters['end_meridian'] = 'pm'
    context['end_hours'] = tuple((value, hour, value == parameters.get('end_hour')) for value, hour in OPTIONS_HOURS)
    context['end_meridians'] = tuple((meridian, meridian == parameters.get('end_meridian')) for meridian in OPTIONS_MERIDIANS)
    return context

Result = namedtuple('Result', ('offering', 'semester', 'course', 'title', 'units', 'instructors', 'meetings', 'core'))

def to_result(offering):
    semester = offering.year + ' ' + offering.season.capitalize()
    course = ' '.join([offering.department, offering.number, offering.section])
    title = offering.title
    units = offering.units
    instructors = []
    for instructor in offering.instructors:
        instructors.append((instructor.last_name, instructor.full_name))
    instructors = sorted(instructors)
    meetings = []
    for meeting in offering.meetings:
        if meeting.start_time is None:
            time = ''
            days = ''
            days_full = ''
            location = 'TBD'
        else:
            time = (meeting.start_time.strftime('%I:%M%p') + '-' + meeting.end_time.strftime('%I:%M%p')).lower()
            days = meeting.days
            days_full = meeting.days_long
            if meeting.location is None:
                location = 'TBD'
            else:
                location = meeting.location
        meetings.append((time, days, days_full, location))
    core = []
    for code in offering.cores:
        core.append((code, CORE_ABBRS[code]))
    core = sorted(core)
    return Result(offering, semester, course, title, units, instructors, meetings, core)

app = Flask(__name__)

@app.route('/')
def view_root():
    parameters = request.args.to_dict()
    if 'semester' in parameters:
        semester = parameters.get('semester')
    else:
        semester = to_semester(*get_current_year_season())
    context = {}
    context = get_search_results(parameters, context)
    context = sort_search_results(parameters, context)
    context = get_dropdown_options(parameters, context, semester)
    if 'sort' in parameters:
        parameters.pop('sort')
    context['url'] = url_for('view_root', **parameters)
    context['advanced'] = str(parameters.get('advanced'))
    return render_template('base.html', **context)

if __name__ == '__main__':
    app.run(debug=True)
