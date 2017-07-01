#!/usr/bin/env python3

from datetime import datetime, date
from collections import namedtuple

from flask import Flask, render_template, request, url_for, redirect

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
    Day('M','Monday'),
    Day('T','Tuesday'),
    Day('W','Wednesday'),
    Day('R','Thursday'),
    Day('F','Friday'),
    Day('U','Saturday'),
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
    # FIXME
    #query = query.join(OfferingMeeting, Meeting, TimeSlot, Room, Building)
    #query = query.join(OfferingCore, Core)
    #query = query.join(OfferingInstructor, Person)
    if parameters:
        query = filter_study_abroad(query)
        semester = get_parameter_or_none(parameters, 'semester')
        if semester is None:
            semester = Semester.current_semester()
        elif semester is not 'any':
            year, season = Semester.code_to_season(semester)
            semester = session.query(Semester).filter(Semester.year == year, Semester.season == season).one()
        else:
            semester = None
        assert semester is None or isinstance(semester, Semester)
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
        if key == 'semester' or key not in DEFAULT_OPTIONS or value != DEFAULT_OPTIONS[key]:
            simplified[key] = value
    return redirect(url_for('view_root', **simplified))

if __name__ == '__main__':
    app.run(debug=True)
