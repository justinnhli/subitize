#!/usr/bin/env python3

from collections import namedtuple
from datetime import datetime
from os.path import exists as file_exists, join as join_path

from flask import Flask, render_template, abort, request, send_from_directory, url_for, redirect
from flask.json import jsonify
from sqlalchemy.sql.expression import asc, desc

from models import create_session
from models import Semester
from models import TimeSlot, Building, Room, Meeting
from models import Core, Department, Course
from models import Person
from models import OfferingMeeting, OfferingCore, OfferingInstructor, Offering
from models import CourseInfo
from subitizelib import filter_study_abroad, filter_by_search
from subitizelib import filter_by_semester, filter_by_department, filter_by_number, filter_by_instructor
from subitizelib import filter_by_units, filter_by_core, filter_by_meeting, filter_by_openness
from subitizelib import sort_offerings

app = Flask(__name__)

Day = namedtuple('Day', ['abbr', 'name'])
Hour = namedtuple('Hour', ['value', 'display'])

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
OPTIONS_HOURS = [
    (lambda time: Hour(time.strftime('%H%M'), time.strftime('%I %p').strip('0').lower()))(
        datetime.strptime(str(i), '%H')
    ) for i in range(6, 24)
]

DEFAULT_OPTIONS = {
    'query': 'search for courses...',
    'semester': Semester.current_semester_code(),
    'open': '',
    'instructor': '',
    'core': '',
    'units': '',
    'department': '',
    'lower': '0',
    'upper': '999',
    'day': '',
    'start_hour': '0600',
    'end_hour': '2300',
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
    context['semesters'] = list(session.query(Semester).order_by(desc(Semester.id)))
    context['instructors'] = sorted(session.query(Person), key=(lambda p: (p.last_name + ', ' + p.first_name).lower()))
    context['cores'] = list(session.query(Core).order_by(Core.name))
    context['units'] = sorted(row[0] for row in session.query(Offering.units).distinct())
    context['departments'] = list(filter_study_abroad(session.query(Department)).order_by(asc(Department.name)))
    context['lower'] = (OPTIONS_LOWER if parameters.get('lower') is None else parameters.get('lower'))
    context['upper'] = (OPTIONS_UPPER if parameters.get('upper') is None else parameters.get('upper'))
    context['days'] = OPTIONS_DAYS
    context['start_hours'] = OPTIONS_HOURS
    context['end_hours'] = OPTIONS_HOURS
    return context


def get_search_results(session, parameters):
    query = session.query(Offering)
    query = query.join(Semester)
    query = query.join(Course, Department)
    query = query.outerjoin(CourseInfo)
    query = query.outerjoin(OfferingMeeting, Meeting, TimeSlot, Room, Building)
    query = query.outerjoin(OfferingCore, Core)
    query = query.outerjoin(OfferingInstructor, Person)
    if not parameters:
        return None
    query = filter_study_abroad(query)
    semester = get_parameter_or_none(parameters, 'semester')
    if semester is None:
        semester = Semester.current_semester_code()
    elif semester == 'any':
        semester = None
    query = filter_by_semester(query, semester)
    if get_parameter_or_none(parameters, 'open'):
        query = filter_by_openness(query)
    query = filter_by_department(query, get_parameter_or_none(parameters, 'department'))
    query = filter_by_number(
        query, get_parameter_or_none(parameters, 'lower'), get_parameter_or_none(parameters, 'upper')
    )
    query = filter_by_units(query, get_parameter_or_none(parameters, 'units'))
    query = filter_by_instructor(query, get_parameter_or_none(parameters, 'instructor'))
    query = filter_by_core(query, get_parameter_or_none(parameters, 'core'))
    day = get_parameter_or_none(parameters, 'day')
    starts_after = datetime.strptime(get_parameter_or_default(parameters, 'start_hour'), '%H%M').time()
    ends_before = datetime.strptime(get_parameter_or_default(parameters, 'end_hour'), '%H%M').time()
    query = filter_by_meeting(query, day, starts_after, ends_before)
    terms = get_parameter_or_none(parameters, 'query')
    query = filter_by_search(query, terms)
    query = sort_offerings(query, get_parameter_or_none(parameters, 'sort'))
    return query


@app.route('/')
def view_root():
    session = create_session()
    parameters = request.args.to_dict()
    context = get_dropdown_options(session, parameters)
    context['advanced'] = parameters.get('advanced')
    if 'semester' not in parameters:
        parameters['semester'] = Semester.current_semester_code()
    context['defaults'] = dict((k, v) for k, v in DEFAULT_OPTIONS.items())
    context['defaults'].update(parameters)
    with open('data/last-update') as fd:
        context['last_update'] = fd.read().strip()
    return render_template('base.html', **context)


@app.route('/json/')
def view_json():
    session = create_session()
    parameters = request.args.to_dict()
    query = get_search_results(session, parameters)
    results = [offering.to_json_dict() for offering in query]
    metadata = {}
    if 'sort' in parameters:
        metadata['sorted'] = parameters['sort']
        del parameters['sort']
    else:
        metadata['sorted'] = 'semester'
    metadata['advanced'] = parameters['advanced']
    metadata['parameters'] = url_for('view_root', **parameters)[2:]
    response = {
        'metadata': metadata,
        'results': results,
    }
    return jsonify(response)


@app.route('/simplify/')
def view_simplify():
    parameters = request.args.to_dict()
    if 'query' in parameters:
        if get_parameter_or_none(parameters, 'query'):
            parameters['query'] = parameters['query'].strip()
        else:
            del parameters['query']
    simplified = {}
    for key, value in parameters.items():
        if key == 'semester' or key not in DEFAULT_OPTIONS or value != DEFAULT_OPTIONS[key]:
            simplified[key] = value
    if 'json' in simplified:
        del simplified['json']
        return redirect(url_for('view_json', **simplified))
    else:
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
