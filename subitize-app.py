#!/usr/bin/env python3

from math import ceil
from datetime import datetime

from flask import Flask, render_template, request, url_for

from models import Semester, Weekday, Core, Department, Faculty, Offering, load_data
from subitizelib import filter_study_abroad, filter_by_search, filter_by_semester, filter_by_department, filter_by_number, filter_by_units, filter_by_instructor, filter_by_core

load_data()

OFFERINGS = tuple(Offering.all())

OPTIONS_SEMESTERS = sorted(Semester.all(), reverse=True)
OPTIONS_INSTRUCTORS = sorted(Faculty.all(), key=(lambda f: f.last_first.lower()))
OPTIONS_CORES = sorted(Core.all(), key=(lambda c: c.name))
OPTIONS_UNITS = sorted(set(o.units for o in OFFERINGS))
OPTIONS_DEPARTMENTS = sorted(Department.all(), key=(lambda d: d.name))
OPTIONS_LOWER = 0
OPTIONS_UPPER = max(ceil(o.course.pure_number_int / 100) * 100 - 1 for o in OFFERINGS)
OPTIONS_DAYS = sorted(Weekday.all())
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
            results = tuple(offering for offering in results if any(meeting.time_slot is None or parameters.get('day') in meeting.time_slot.weekdays_abbreviation for meeting in offering.meetings))
        start_hour = datetime.strptime(parameters.get('start_hour') + parameters.get('start_meridian'), '%I%p').time()
        results = tuple(offering for offering in results if all((meeting.time_slot is None or start_hour < meeting.time_slot.start_time) for meeting in offering.meetings))
        end_hour = datetime.strptime(parameters.get('end_hour') + parameters.get('end_meridian'), '%I%p').time()
        results = tuple(offering for offering in results if all((meeting.time_slot is None or meeting.time_slot.end_time < end_hour) for meeting in offering.meetings))
        context['results'] = tuple(results)
        if parameters.get('query').strip() == '':
            context['query'] = 'search for courses...'
        else:
            context['query'] = parameters.get('query')
    return context

def sort_search_results(parameters, context):
    if 'sort' in parameters:
        field = parameters.get('sort')
        if field == 'semester':
            context['results'] = sorted(context['results'], key=(lambda offering: offering.semester))
        elif field == 'course':
            context['results'] = sorted(context['results'], key=(lambda offering: (offering.department.code, offering.number)))
        elif field == 'title':
            context['results'] = sorted(context['results'], key=(lambda offering: offering.name))
        elif field == 'units':
            context['results'] = sorted(context['results'], key=(lambda offering: offering.units))
        elif field == 'instructor':
            context['results'] = sorted(context['results'], key=(lambda offering: sorted(i.last_name for i in offering.instructors)))
        elif field == 'meetings':
            context['results'] = sorted(context['results'], key=(lambda offering: sorted(offering.meetings)))
        elif field == 'cores':
            context['results'] = sorted(context['results'], key=(lambda offering: sorted(c.code for c in offering.cores)))
    return context

def get_dropdown_options(parameters, context):
    context['semesters'] = OPTIONS_SEMESTERS
    context['instructors'] = OPTIONS_INSTRUCTORS
    context['cores'] = OPTIONS_CORES
    context['units'] = OPTIONS_UNITS
    context['departments'] = OPTIONS_DEPARTMENTS
    context['lower'] = (OPTIONS_LOWER if parameters.get('lower') is None else parameters.get('lower'))
    context['upper'] = (OPTIONS_UPPER if parameters.get('upper') is None else parameters.get('upper'))
    context['days'] = OPTIONS_DAYS
    context['start_hours'] = tuple((value, hour, value == parameters.get('start_hour')) for value, hour in OPTIONS_HOURS)
    context['start_meridians'] = tuple((meridian, meridian == parameters.get('start_meridian')) for meridian in OPTIONS_MERIDIANS)
    if len(parameters) == 0:
        parameters['end_hour'] = '11'
        parameters['end_meridian'] = 'pm'
    context['end_hours'] = tuple((value, hour, value == parameters.get('end_hour')) for value, hour in OPTIONS_HOURS)
    context['end_meridians'] = tuple((meridian, meridian == parameters.get('end_meridian')) for meridian in OPTIONS_MERIDIANS)
    return context

app = Flask(__name__)

@app.route('/')
def view_root():
    parameters = request.args.to_dict()
    context = {}
    context = get_search_results(parameters, context)
    context = sort_search_results(parameters, context)
    context = get_dropdown_options(parameters, context)
    if 'sort' in parameters:
        parameters.pop('sort')
    context['url'] = url_for('view_root', **parameters)
    context['advanced'] = str(parameters.get('advanced'))
    if 'semester' not in parameters:
        parameters['semester'] = Semester.current_semester().code
    context['parameters'] = parameters
    return render_template('base.html', **context)

if __name__ == '__main__':
    app.run(debug=True)
