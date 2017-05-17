#!/usr/bin/env python3

from datetime import datetime
from math import ceil
from os.path import exists as file_exists, join as join_path

from flask import Flask, render_template, request, send_from_directory, url_for, redirect

from models import Semester, Weekday, Core, Department, Faculty, Offering
from subitizelib import filter_study_abroad, filter_by_search, filter_by_semester, filter_by_openness, filter_by_department, filter_by_number, filter_by_units, filter_by_instructor, filter_by_core, filter_by_meeting
from subitizelib import sort_offerings

OFFERINGS = tuple(Offering.all())

OPTIONS_SEMESTERS = sorted(Semester.all(), reverse=True)
OPTIONS_INSTRUCTORS = sorted(Faculty.all(), key=(lambda f: f.last_first.lower()))
OPTIONS_CORES = sorted(Core.all(), key=(lambda c: c.name))
OPTIONS_UNITS = sorted(set(o.units for o in OFFERINGS))
OPTIONS_DEPARTMENTS = sorted(Department.all(), key=(lambda d: d.name))
OPTIONS_LOWER = 0
OPTIONS_UPPER = max(ceil(o.course.pure_number_int / 100) * 100 - 1 for o in OFFERINGS)
OPTIONS_DAYS = sorted(Weekday.all())
OPTIONS_HOURS = [datetime.strptime(str(i), '%H').strftime('%I %p').strip('0').lower() for i in range(6, 24)]

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
    'start_hour': '6 am',
    'end_hour': '11 pm',
}

def get_parameter_or_none(parameters, parameter):
    if parameter not in parameters:
        return None
    if parameter not in DEFAULT_OPTIONS:
        return parameters[parameter]
    value = parameters.get(parameter)
    default = DEFAULT_OPTIONS[parameter]
    if value != '' and value != default:
        return value
    else:
        return None

def get_parameter_or_default(parameters, parameter):
    value = get_parameter_or_none(parameters, parameter)
    if value:
        return value
    else:
        assert parameter in DEFAULT_OPTIONS
        return DEFAULT_OPTIONS[parameter]

def get_dropdown_options(parameters):
    context = {}
    context['semesters'] = OPTIONS_SEMESTERS
    context['instructors'] = OPTIONS_INSTRUCTORS
    context['cores'] = OPTIONS_CORES
    context['units'] = OPTIONS_UNITS
    context['departments'] = OPTIONS_DEPARTMENTS
    context['lower'] = (OPTIONS_LOWER if parameters.get('lower') is None else parameters.get('lower'))
    context['upper'] = (OPTIONS_UPPER if parameters.get('upper') is None else parameters.get('upper'))
    context['days'] = OPTIONS_DAYS
    context['start_hours'] = OPTIONS_HOURS
    context['end_hours'] = OPTIONS_HOURS
    return context

def get_search_results(parameters, context):
    if parameters:
        results = filter_study_abroad(OFFERINGS)
        results = filter_by_search(results, get_parameter_or_none(parameters, 'query'))
        semester = get_parameter_or_none(parameters, 'semester')
        if semester == '':
            semester = None
        results = filter_by_semester(results, semester)
        if get_parameter_or_none(parameters, 'open'):
            results = filter_by_openness(results)
        results = filter_by_department(results, get_parameter_or_none(parameters, 'department'))
        results = filter_by_number(results, get_parameter_or_none(parameters, 'lower'), get_parameter_or_none(parameters, 'upper'))
        results = filter_by_units(results, get_parameter_or_none(parameters, 'units'))
        results = filter_by_instructor(results, get_parameter_or_none(parameters, 'instructor'))
        results = filter_by_core(results, get_parameter_or_none(parameters, 'core'))
        day = get_parameter_or_none(parameters, 'day')
        starts_after = datetime.strptime(get_parameter_or_default(parameters, 'start_hour'), '%I %p').time()
        ends_before = datetime.strptime(get_parameter_or_default(parameters, 'end_hour'), '%I %p').time()
        results = filter_by_meeting(results, day, starts_after, ends_before)
        context['results'] = tuple(results)
    else:
        context['results'] = None
    return context

def sort_search_results(parameters, context):
    if context['results'] is not None:
        context['results'] = sort_offerings(context['results'], get_parameter_or_none(parameters, 'sort'))
    return context

app = Flask(__name__)

@app.route('/')
def view_root():
    parameters = request.args.to_dict()
    context = get_dropdown_options(parameters)
    context = get_search_results(parameters, context)
    context = sort_search_results(parameters, context)
    if 'sort' in parameters:
        parameters.pop('sort')
    context['parameters'] = parameters
    context['base_url'] = url_for('view_root')
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
    if get_parameter_or_none(parameters, 'query'):
        parameters['query'] = parameters['query'].strip()
    else:
        del parameters['query']
    simplified = {}
    for key, value in parameters.items():
        if key not in DEFAULT_OPTIONS or value != DEFAULT_OPTIONS[key]:
            simplified[key] = value
    return redirect(url_for('view_root', **simplified))

@app.route('/static/css/<file>')
def get_css(file):
    if file_exists(join_path('static/css', file)):
        return send_from_directory('static/css', file)
    else:
        return abort(404)

if __name__ == '__main__':
    app.run(debug=True)
