#!/usr/bin/env python3

# pylint: disable = wrong-import-position

"""The subitize web-app."""

from collections import namedtuple
from copy import copy
from datetime import datetime
from pathlib import Path
from time import sleep

from flask import Flask, render_template, abort, request, send_from_directory, url_for, redirect
from flask.json import jsonify
from sqlalchemy.sql.expression import asc, desc

from .models import create_session
from .models import Semester, Core, Department, Person, Offering
from .subitizelib import create_query
from .subitizelib import filter_study_abroad, filter_by_search
from .subitizelib import filter_by_semester, filter_by_department, filter_by_instructor
from .subitizelib import filter_by_number, filter_by_number_str, filter_by_section
from .subitizelib import filter_by_units, filter_by_core, filter_by_meeting, filter_by_openness
from .subitizelib import sort_offerings

Day = namedtuple('Day', ['abbr', 'name'])
Hour = namedtuple('Hour', ['value', 'display'])

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


def create_context_template():
    """Create a context template with the advanced search options values.

    Returns:
        dict: The context.
    """
    session = create_session()
    hours = [
        (lambda time: Hour(time.strftime('%H%M'), time.strftime('%I %p').strip('0').lower()))(
            datetime.strptime(str(i), '%H')
        ) for i in range(6, 24)
    ]
    return {
        'semesters': list(session.query(Semester).order_by(desc(Semester.id))),
        'instructors': sorted(session.query(Person), key=(lambda p: (p.last_name + ', ' + p.first_name).lower())),
        'cores': list(session.query(Core).order_by(Core.name)),
        'units': [
            str(unit) for unit in
            sorted(row[0] for row in session.query(Offering.units).distinct())
        ],
        'departments': list(session.query(Department).filter( # pylint: disable = no-member
            Department.code != 'OXAB',
            Department.code.notilike('AB%'),
        ).order_by(asc(Department.name))),
        'lower': 0,
        'upper': 999,
        'days': [
            Day('M', 'Monday'),
            Day('T', 'Tuesday'),
            Day('W', 'Wednesday'),
            Day('R', 'Thursday'),
            Day('F', 'Friday'),
            Day('U', 'Saturday'),
        ],
        'start_hours': hours,
        'end_hours': hours,
    }


CONTEXT_TEMPLATE = create_context_template()

JSON_RESULT_LIMIT = 200

ROOT_DIRECTORY = Path(__file__).resolve().parent
LAST_UPDATE_FILE = ROOT_DIRECTORY / 'data' / 'last-update'

VALID_SORTS = set(['semester', 'course', 'title', 'units', 'instructors', 'meetings', 'cores'])


def get_parameter_or_none(parameters, parameter):
    """Get a parameter if it is not its default value.

    Argument:
        parameters (dict): The dictionary of parameters and values.
        parameter (str): The parameter to get.

    Returns:
        str: The value of the parameter.
    """
    if parameter not in parameters:
        return None
    if parameter not in DEFAULT_OPTIONS:
        return parameters[parameter]
    value = parameters.get(parameter)
    default = DEFAULT_OPTIONS[parameter]
    if value not in ('', default):
        return value
    else:
        return None


def get_search_results(session, parameters):
    """Build a query for the search.

    Arguments:
        session (Session): The sqlalchemy session to connect with.
        parameters (dict): The parameters of the current search.

    Returns:
        Query: A sqlalchemy Query object representing the search.
    """
    # create query and filter out study abroad courses
    query = create_query(session)
    if not parameters:
        return query.limit(JSON_RESULT_LIMIT)
    query = filter_study_abroad(session, query)
    # filter by semester
    semester = get_parameter_or_none(parameters, 'semester')
    if semester is None:
        semester = Semester.current_semester_code()
    elif semester == 'any':
        semester = None
    query = filter_by_semester(session, query, semester)
    # filter by advanced options
    if get_parameter_or_none(parameters, 'open'):
        query = filter_by_openness(session, query)
    query = filter_by_department(session, query, get_parameter_or_none(parameters, 'department'))
    query = filter_by_number(
        session,
        query,
        get_parameter_or_none(parameters, 'lower'),
        get_parameter_or_none(parameters, 'upper'),
    )
    query = filter_by_units(session, query, get_parameter_or_none(parameters, 'units'))
    query = filter_by_instructor(session, query, get_parameter_or_none(parameters, 'instructor'))
    query = filter_by_core(session, query, get_parameter_or_none(parameters, 'core'))
    query = filter_by_meeting(
        session,
        query,
        get_parameter_or_none(parameters, 'day'),
        get_parameter_or_none(parameters, 'start_hour'),
        get_parameter_or_none(parameters, 'end_hour'),
    )
    # filter by search
    query = filter_by_search(session, query, get_parameter_or_none(parameters, 'query'))
    # sort results
    sort = get_parameter_or_none(parameters, 'sort')
    if sort is not None and sort not in VALID_SORTS:
        raise abort(400)
    query = sort_offerings(session, query, sort)
    # return
    return query.limit(JSON_RESULT_LIMIT)


app = Flask(__name__, root_path=ROOT_DIRECTORY) # pylint: disable = invalid-name


@app.route('/')
def view_root():
    """Serve the homepage."""
    parameters = request.args.to_dict()
    context = copy(CONTEXT_TEMPLATE)
    if parameters.get('lower') is not None:
        context['lower'] = parameters.get('lower')
    if parameters.get('upper') is not None:
        context['upper'] = parameters.get('upper')
    context['advanced'] = parameters.get('advanced')
    if 'semester' not in parameters:
        parameters['semester'] = Semester.current_semester_code()
    context['defaults'] = dict((k, v) for k, v in DEFAULT_OPTIONS.items())
    context['defaults'].update(parameters)
    with LAST_UPDATE_FILE.open() as fd:
        context['last_update'] = fd.read().strip()
    return render_template('main.html', **context)


@app.route('/json/')
def view_json():
    """Serve the JSON endpoint."""
    session = create_session()
    parameters = request.args.to_dict()
    query = get_search_results(session, parameters)
    results = [offering.to_json_dict() for offering in query.all()]
    metadata = {}
    if 'sort' in parameters:
        metadata['sorted'] = parameters['sort']
        del parameters['sort']
    else:
        metadata['sorted'] = 'semester'
    if 'advanced' in parameters:
        metadata['advanced'] = parameters['advanced']
    metadata['parameters'] = url_for('view_root', **parameters)[2:]
    response = {
        'metadata': metadata,
        'results': results,
    }
    return jsonify(response)


@app.route('/simplify/')
def view_simplify():
    """Redirect the request with simplified parameters."""
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


@app.route('/fetch/<readable_ids>')
def view_fetch(readable_ids):
    """Fetch the details of one or more comma-separated offerings."""
    session = create_session()
    offerings = []
    for readable_id in readable_ids.split(','):
        semester, department, number, section = readable_id.split('_')
        query = create_query(session)
        query = filter_by_semester(session, query, semester)
        query = filter_by_department(session, query, department)
        query = filter_by_number_str(session, query, number)
        query = filter_by_section(session, query, section)
        offering = query.first()
        if offering is not None:
            offerings.append(offering)
    return jsonify({
        offering.readable_id: offering.to_json_dict()
        for offering in offerings
    })


@app.route('/json-doc/')
def view_json_doc():
    """Serve the JSON API description page."""
    return render_template('api.html')


@app.route('/static/css/<file>')
def get_css(file):
    """Serve CSS files."""
    file_dir = ROOT_DIRECTORY / 'static' / 'css'
    file_path = file_dir / file
    if file_path.exists():
        return send_from_directory(file_dir, file)
    else:
        return abort(404)


@app.route('/static/js/<file>')
def get_js(file):
    """Serve JavaScript files."""
    file_dir = ROOT_DIRECTORY / 'static' / 'js'
    file_path = file_dir / file
    if file_path.exists():
        return send_from_directory(file_dir, file)
    else:
        return abort(404)
