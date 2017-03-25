#!/usr/bin/env python3

def filter_study_abroad(offerings):
    return tuple(o for o in offerings if not (o.course.department.code == 'OXAB' or o.course.department.code.startswith('AB')))

def filter_by_search(offerings, query=None):
    if query is None:
        return offerings
    terms = query.lower().split()
    results = []
    for offering in offerings:
        match = True
        for term in terms:
            if term in offering.name.lower():
                continue
            if term == offering.course.department.code.lower() or term in offering.course.department.name.lower():
                continue
            if term == offering.course.pure_number_str:
                continue
            if any((term in instructor.full_name.lower()) for instructor in offering.instructors if instructor is not None):
                continue
            if any((term in core.code.lower() or term in core.name.lower()) for core in offering.cores):
                continue
            match = False
            break
        if match:
            results.append(offering)
    return tuple(results)

def filter_by_semester(offerings, semester=None):
    if semester is None:
        return offerings
    return tuple(offering for offering in offerings if offering.semester.code == semester)

def filter_by_openness(offerings):
    return tuple(offering for offering in offerings if offering.is_open)

def filter_by_instructor(offerings, instructor=None):
    if instructor is None:
        return offerings
    return tuple(offering for offering in offerings if any(instructor == o_instructor.alias for o_instructor in offering.instructors if o_instructor))

def filter_by_core(offerings, core=None):
    if core is None:
        return offerings
    return tuple(offering for offering in offerings for o_core in offering.cores if core == o_core.code)

def filter_by_units(offerings, units=None):
    if units is None:
        return offerings
    return tuple(offering for offering in offerings if offering.units == int(units))

def filter_by_department(offerings, department=None):
    if department is None:
        return offerings
    return tuple(offering for offering in offerings if offering.course.department.code == department)

def filter_by_number(offerings, minimum=None, maximum=None):
    if minimum is not None and maximum is not None:
        return tuple(offering for offering in offerings if int(minimum) <= offering.course.pure_number_int <= int(maximum))
    elif maximum is not None:
        return tuple(offering for offering in offerings if offering.course.pure_number_int <= int(maximum))
    elif minimum is not None:
        return tuple(offering for offering in offerings if int(minimum) <= offering.course.pure_number_int)
    else:
        return offerings

def filter_by_meeting(offerings, day=None, starts_after=None, ends_before=None):
    if day is None and starts_after is None and ends_before is None:
        return offerings
    result = []
    for offering in offerings:
        for meeting in offering.meetings:
            passes = True
            if meeting.time_slot is None:
                passes = True
                break
            if day is not None and day not in meeting.weekdays_abbreviation:
                passes = False
            if starts_after is not None and meeting.start_time < starts_after:
                passes = False
            if ends_before is not None and ends_before < meeting.end_time:
                passes = False
            if passes:
                break
        if passes:
            result.append(offering)
    return tuple(result)

def sort_offerings(offerings, field=None, reverse=False):
    if field is None:
        key_fn = (lambda offering: (-int(offering.semester.code), offering.department, offering.course.pure_number_int, offering.course.number, offering.section))
    elif field == 'semester':
        key_fn = (lambda offering: -int(offering.semester))
    elif field == 'course':
        key_fn = (lambda offering: (offering.department.code, offering.number, offering.section))
    elif field == 'title':
        key_fn = (lambda offering: offering.name.lower())
    elif field == 'units':
        key_fn = (lambda offering: offering.units)
    elif field == 'instructors':
        key_fn = (lambda offering: sorted(i.last_name.lower() for i in offering.instructors if i))
    elif field == 'meetings':
        key_fn = (lambda offering: sorted(offering.meetings))
    elif field == 'cores':
        key_fn = (lambda offering: sorted(c.code for c in offering.cores))
    else:
        raise ValueError('invalid sorting key: {}'.format(field))
    return sorted(offerings, key=key_fn, reverse=reverse)
