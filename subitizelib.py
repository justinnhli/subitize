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
            match = False
            break
        if match:
            results.append(offering)
    return tuple(results)

def filter_by_semester(offerings, semester=None):
    if semester is None:
        return offerings
    return tuple(offering for offering in offerings if offering.semester.code == semester)

def filter_by_department(offerings, department=None):
    if department is None:
        return offerings
    return tuple(offering for offering in offerings if offering.course.department.code == department)

def filter_by_number(offerings, minimum=None, maximum=None):
    if minimum is None or maximum is None:
        return offerings
    elif minimum is None:
        return tuple(offering for offering in offerings if offering.course.pure_number_int <= int(maximum))
    elif maximum is None:
        return tuple(offering for offering in offerings if int(minimum) <= offering.course.pure_number_int)
    else:
        return tuple(offering for offering in offerings if int(minimum) <= offering.course.pure_number_int <= int(maximum))

def filter_by_units(offerings, units=None):
    if units is None:
        return offerings
    return tuple(offering for offering in offerings if offering.units == int(units))

def filter_by_instructor(offerings, instructor=None):
    if instructor is None:
        return offerings
    return tuple(offering for offering in offerings if any(instructor == o_instructor.alias for o_instructor in offering.instructors if o_instructor))

def filter_by_core(offerings, core=None):
    if core is None:
        return offerings
    return tuple(offering for offering in offerings for o_core in offering.cores if core == o_core.code)
