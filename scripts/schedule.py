#!/usr/bin/env python3

import sys
from pathlib import Path
from itertools import product
from collections import defaultdict

ROOT_DIRECTORY = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIRECTORY))

from subitize import create_session, create_select, filter_by_department, filter_by_semester


def meetings_str(offering):
    if not offering.meetings:
        return 'Time TBD (Location TBD)'
    return '; '.join(
        str(meeting.timeslot) for meeting in offering.meetings
    )


def has_conflict(offering1, offering2):
    for meeting1 in offering1.meetings:
        weekdays1 = set(meeting1.weekdays)
        for meeting2 in offering2.meetings:
            if not weekdays1.intersection(meeting2.weekdays):
                continue
            if meeting1.timeslot.start <= meeting2.timeslot.start <= meeting1.timeslot.end:
                return True
            if meeting2.timeslot.start <= meeting1.timeslot.start <= meeting2.timeslot.end:
                return True
    return False


def component_schedules(component, graph, schedule=None):
    if schedule is None:
        schedule = {}
    if len(schedule) == len(component):
        return set([frozenset([
            offering for offering, offered in schedule.items() if offered
        ]),])
    schedules = set()
    for offering in (component - set(schedule)):
        new_schedule = dict(schedule.items())
        new_schedule[offering] = True
        for neighbor in graph[offering]:
            new_schedule[neighbor] = False
        schedules.update(component_schedules(
            component,
            graph,
            new_schedule,
        ))
    return schedules


def connected_components(graph):
    nodes = set(graph)
    components = []
    for node in graph:
        if node not in nodes:
            continue
        # find connected components
        component = set([node,])
        frontier = [node,]
        while frontier:
            node = frontier.pop(0)
            if node not in nodes:
                continue
            nodes.discard(node)
            component.add(node)
            frontier.extend(
                neighbor for neighbor in graph[node]
                if neighbor in nodes
            )
        components.append(component)
    return components


def valid_schedule(schedule):
    for offering1 in schedule:
        for offering2 in schedule:
            if offering1 is not offering2 and has_conflict(offering1, offering2):
                return False
    return True


def generate_schedules(offerings):
    # detect conflicts
    no_conflicts = set(offerings)
    graph = defaultdict(set)
    for i, offering1 in enumerate(offerings):
        for offering2 in offerings[i+1:]:
            if has_conflict(offering1, offering2):
                graph[offering1].add(offering2)
                graph[offering2].add(offering1)
                no_conflicts.discard(offering1)
                no_conflicts.discard(offering2)
    # generate possibilities for each connected component
    disjoint_schedules = [
        component_schedules(component, graph) for component
        in connected_components(graph)
    ]
    schedules  = []
    for partial_schedules in product(*disjoint_schedules):
        schedule = set(no_conflicts)
        for partial_schedule in partial_schedules:
            schedule.update(partial_schedule)
        assert valid_schedule(schedule)
        schedules.append(schedule)
    return schedules


def main():
    # find offerings
    session = create_session()
    statement = create_select()
    statement = filter_by_semester(statement, '202402')
    statement = filter_by_department(statement, 'COMP')
    offerings = []
    for offering in session.scalars(statement):
        if offering.course.number_int > 146:
            offerings.append(offering)
    offerings = sorted(offerings, key=str)
    schedules = generate_schedules(offerings)
    for schedule in schedules:
        for offering in sorted(schedule, key=str):
            print(f'{offering}: {meetings_str(offering)}')
        print()
    print(len(schedules))


if __name__ == '__main__':
    main()
