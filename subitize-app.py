#!/usr/bin/env python3

from collections import namedtuple
from datetime import datetime
from os.path import exists as file_exists, join as join_path

from flask import Flask, render_template, abort, request, send_from_directory, url_for, redirect

from models import create_session
from models import Semester
from models import TimeSlot, Building, Room, Meeting
from models import Core, Department, Course
from models import Person
from models import OfferingMeeting, OfferingCore, OfferingInstructor, Offering
from subitizelib import filter_study_abroad, filter_by_search, filter_by_semester, filter_by_openness, filter_by_department, filter_by_number, filter_by_units, filter_by_instructor, filter_by_core, filter_by_meeting
from subitizelib import sort_offerings

app = Flask(__name__)

Day = namedtuple('Day', ['abbr', 'name'])

OPTIONS_LOWER = 0
OPTIONS_UPPER = 999
OPTIONS_DAYS = [
    Day('M', 'Monday'),
    Day('T', 'Tuesday'),
    Day('W', 'Wednesday'),
    Day('R', 'Thursday'),
    Day('F', 'Friday'),
    Day('U', 'Saturday'),
]
OPTIONS_HOURS = [datetime.strptime(str(i), '%H').strftime('%I %p').strip('0').lower() for i in range(6, 24)]

DEFAULT_OPTIONS = {
    'query': 'search for courses...',
    'semester': Semester.current_semester().code,
    'open': '',
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

def get_dropdown_options(session, parameters):
    context = {}
    context['semesters'] = sorted(session.query(Semester), reverse=True)
    context['instructors'] = sorted(session.query(Person), key=(lambda p: (p.last_name + ', ' + p.first_name).lower()))
    context['cores'] = sorted(session.query(Core), key=(lambda c: c.name))
    context['units'] = sorted(row[0] for row in session.query(Offering.units).distinct())
    context['departments'] = sorted(session.query(Department), key=(lambda d: d.name))
    context['lower'] = (OPTIONS_LOWER if parameters.get('lower') is None else parameters.get('lower'))
    context['upper'] = (OPTIONS_UPPER if parameters.get('upper') is None else parameters.get('upper'))
    context['days'] = OPTIONS_DAYS
    context['start_hours'] = OPTIONS_HOURS
    context['end_hours'] = OPTIONS_HOURS
    return context

def get_search_results(session, parameters, context):
    query = session.query(Offering)
    query = query.join(Semester)
    query = query.join(Course, Department)
    query = query.outerjoin(OfferingMeeting, Meeting, TimeSlot, Room, Building)
    query = query.outerjoin(OfferingCore, Core)
    query = query.outerjoin(OfferingInstructor, Person)
    if parameters:
        query = filter_study_abroad(query)
        semester = get_parameter_or_none(parameters, 'semester')
        if semester is None:
            semester = Semester.current_semester().code
        elif semester == 'any':
            semester = None
        query = filter_by_semester(query, semester)
        if get_parameter_or_none(parameters, 'open'):
            query = filter_by_openness(query)
        department = get_parameter_or_none(parameters, 'department')
        if department is not None:
            department = session.query(Department).filter(Department.code == department).one()
        query = filter_by_department(query, department)
        query = filter_by_number(query, get_parameter_or_none(parameters, 'lower'), get_parameter_or_none(parameters, 'upper'))
        query = filter_by_units(query, get_parameter_or_none(parameters, 'units'))
        query = filter_by_instructor(query, get_parameter_or_none(parameters, 'instructor'))
        query = filter_by_core(query, get_parameter_or_none(parameters, 'core'))
        day = get_parameter_or_none(parameters, 'day')
        starts_after = datetime.strptime(get_parameter_or_default(parameters, 'start_hour'), '%I %p').time()
        ends_before = datetime.strptime(get_parameter_or_default(parameters, 'end_hour'), '%I %p').time()
        query = filter_by_meeting(query, day, starts_after, ends_before)
        terms = get_parameter_or_none(parameters, 'query')
        query = filter_by_search(query, terms)
        query = sort_offerings(query, get_parameter_or_none(parameters, 'sort'))
        context['results'] = []
        for offering in query:
            context['results'].append(offering)
    else:
        context['results'] = None
    return context

@app.route('/')
def view_root():
    session = create_session()
    parameters = request.args.to_dict()
    context = get_dropdown_options(session, parameters)
    context = get_search_results(session, parameters, context)
    if 'sort' in parameters:
        context['cur_sort'] = parameters['sort']
        parameters.pop('sort')
    else:
        context['cur_sort'] = 'semester'
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
        if key == 'semester' or key not in DEFAULT_OPTIONS or value != DEFAULT_OPTIONS[key]:
            simplified[key] = value
    return redirect(url_for('view_root', **simplified))

@app.route('/static/css/<file>')
def get_css(file):
    if file_exists(join_path('static/css', file)):
        return send_from_directory('static/css', file)
    else:
        return abort(404)

@app.route('/static/js/<file>')
def get_js(file):
    if file_exists(join_path('static/js', file)):
        return send_from_directory('static/js', file)
    else:
        return abort(404)

if __name__ == '__main__':
    app.run(debug=True)
