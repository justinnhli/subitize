#!/usr/bin/env python3

from datetime import datetime
from math import ceil

from flask import Flask, render_template, request, url_for, redirect

from models import Semester, Weekday, Core, Department, Faculty, Offering, load_data
from subitizelib import filter_study_abroad, filter_by_search, filter_by_semester, filter_by_openness, filter_by_department, filter_by_number, filter_by_units, filter_by_instructor, filter_by_core, filter_by_meeting
from subitizelib import sort_offerings

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

DEFAULT_OPTIONS = {
    'query': 'search for courses...',
    'semester': str(Semester.current_semester()),
    'open': '',
    'advanced': 'False',
    'instructor': '',
    'core': '',
    'units': '',
    'department': '',
    'lower': '0',
    'upper': '999',
    'day': '',
    'start_hour': '12',
    'start_meridian': 'am',
    'end_hour': '11',
    'end_meridian': 'pm',
}

def get_parameter(parameters, parameter):
    if parameter not in parameters:
        return None
    if parameter not in DEFAULT_OPTIONS:
        return parameters[parameter]
    value = parameters.get(parameter)
    if value != DEFAULT_OPTIONS[parameter]:
        return value
    else:
        return None

def get_parameter_or_default(parameters, parameter):
    if get_parameter(parameters, parameter):
        return get_parameter(parameters, parameter)
    else:
        assert parameter in DEFAULT_OPTIONS
        return DEFAULT_OPTIONS[parameter]

def get_search_results(parameters, context):
    if len(parameters) == 0:
        context['results'] = None
    else:
        results = filter_study_abroad(OFFERINGS)
        results = filter_by_search(results, get_parameter(parameters, 'query'))
        results = filter_by_semester(results, get_parameter_or_default(parameters, 'semester'))
        if get_parameter(parameters, 'open'):
            results = filter_by_openness(results)
        results = filter_by_department(results, get_parameter(parameters, 'department'))
        results = filter_by_number(results, get_parameter(parameters, 'lower'), get_parameter(parameters, 'upper'))
        results = filter_by_units(results, get_parameter(parameters, 'units'))
        results = filter_by_instructor(results, get_parameter(parameters, 'instructor'))
        results = filter_by_core(results, get_parameter(parameters, 'core'))
        day = get_parameter(parameters, 'day')
        start_hour = get_parameter_or_default(parameters, 'start_hour')
        start_meridian = get_parameter_or_default(parameters, 'start_meridian')
        starts_after = datetime.strptime(start_hour + start_meridian, '%I%p').time()
        end_hour = get_parameter_or_default(parameters, 'end_hour')
        end_meridian = get_parameter_or_default(parameters, 'end_meridian')
        ends_before = datetime.strptime(end_hour + end_meridian, '%I%p').time()
        results = filter_by_meeting(results, day, starts_after, ends_before)
        context['results'] = tuple(results)
    return context

def sort_search_results(parameters, context):
    if context['results'] is not None:
        context['results'] = sort_offerings(context['results'], get_parameter(parameters, 'sort'))
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
    context['start_hours'] = OPTIONS_HOURS
    context['start_meridians'] = OPTIONS_MERIDIANS
    context['end_hours'] = OPTIONS_HOURS
    context['end_meridians'] = OPTIONS_MERIDIANS
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
    context['defaults'] = dict((k, v) for k, v in DEFAULT_OPTIONS.items())
    context['defaults'].update(parameters)
    return render_template('base.html', **context)

@app.route('/simplify/')
def view_simplify():
    parameters = request.args.to_dict()
    got = get_parameter(parameters, 'query')
    if got:
        parameters['query'] = parameters['query'].strip()
    else:
        del parameters['query']
    simplified = {}
    for key, value in parameters.items():
        if key not in DEFAULT_OPTIONS or value != DEFAULT_OPTIONS[key]:
            simplified[key] = value
    return redirect(url_for('view_root', **simplified))

if __name__ == '__main__':
    app.run(debug=True)
