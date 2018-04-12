#!/usr/bin/env python3

import re
import sys
from urllib.parse import urljoin
from os.path import dirname, realpath

import requests
from bs4 import BeautifulSoup
from bs4.element import Comment

sys.path.insert(0, dirname(dirname(realpath(__file__))))

from models import create_session, get_or_create
from models import Department, Course, CourseInfo

BASE_URL = 'http://smartcatalog.co/Catalogs/Occidental-College/{}-{}/Catalog/Courses/'


def get_year_URL(year):
    return BASE_URL.format(year - 1, year)


def get_soup_from_URL(url):
    response = requests.get(url)
    assert response.status_code == 200, 'Downloading {} resulted in HTML status {}'.format(url, response.status_code)
    return BeautifulSoup(response.text, 'html.parser')


def is_valid_url(url):
    return re.search('/[A-Z]+-[^/]+$', url)


def is_preferred_url(url):
    return re.search('Courses/[A-Z]+-[^/]*/[0-9]+/[A-Z]+-[^/]+$', url)


def clean_soup(soup):
    for tag in soup.select('a'):
        tag.unwrap()
    changed = True
    while changed:
        changed = False
        for tag in soup.select('*'):
            if tag.string and not tag.string.strip():
                tag.extract()
                changed = True
    for tag in soup.find_all(text=lambda text: isinstance(text, Comment)):
        tag.extract()
    return soup


def extract_section(section):
    heading = section.contents[0].get_text().strip()
    body = ' '.join(str(contents) for contents in section.contents[1:]).strip()
    return heading, body


def extract_basic_info(session, course_soup):
    dept, number = course_soup.select('h1')[0].get_text().split(' ')[:2]
    dept = dept.strip()
    number = number.strip()
    department = get_or_create(session, Department, code=dept)
    description = str(clean_soup(course_soup.select('div.desc')[0]))
    if description:
        description = re.sub(r'\s+', ' ', description)
    else:
        description = None
    return department, number, description


def extract_prerequisites(course_soup):
    contents = str(course_soup.select('#main')[0])
    sections = []
    last_pos = 0
    for match in re.finditer('<h[2-6]>', contents.lower()):
        section_soup = BeautifulSoup(contents[last_pos:match.start()], 'html.parser')
        if section_soup.get_text().strip():
            sections.append(section_soup)
        last_pos = match.start()
    sections.append(BeautifulSoup(contents[last_pos:], 'html.parser'))
    prerequisites = None
    corequisites = None
    for section_soup in sections[1:]:
        children = [tag for tag in section_soup.contents if hasattr(tag, 'strings') or tag.strip()]
        if len(children) >= 2:
            key, body = extract_section(section_soup)
            if key == 'Prerequisite':
                prerequisites = str(clean_soup(BeautifulSoup(body, 'html.parser')))
                prerequisites = re.sub(r'\s+', ' ', prerequisites)
            elif key == 'Corequisite':
                corequisites = str(clean_soup(BeautifulSoup(body, 'html.parser')))
                corequisites = re.sub(r'\s+', ' ', corequisites)
    return prerequisites, corequisites


def parse_prerequisites(prerequisites):
    pass # TODO


def extract_course_info(session, url):
    if not is_valid_url(url):
        return
    course_soup = get_soup_from_URL(url)
    department, number, description = extract_basic_info(session, course_soup)
    prerequisites, corequisites = extract_prerequisites(course_soup)
    parsed_prerequisites = parse_prerequisites(prerequisites)
    for number in re.split('[/-]', number):
        number = number.strip()
        if not number:
            continue
        course = get_or_create(
            session, Course, department=department, number=number, number_int=int(re.sub('[^0-9]', '', number))
        )
        course_info = session.query(CourseInfo).filter(CourseInfo.course_id == course.id).first()
        if course_info:
            if is_preferred_url(course_info.url):
                pass # TODO detect if prerequisites have changed
            elif is_preferred_url(url):
                course_info.url = url
        else:
            course_info = get_or_create(session, CourseInfo, course_id=course.id, url=url)
        course_info.description = description
        course_info.prerequisites = prerequisites
        course_info.corequisites = corequisites
        course_info.parsed_prerequisites = parsed_prerequisites
        # TODO detect if prerequisites have changed


def test():
    courses = [
        'http://smartcatalog.co/en/Catalogs/Occidental-College/2016-2017/Catalog/Courses/SPAN-Spanish/300/SPAN-378-379',
        'http://smartcatalog.co/Catalogs/Occidental-College/2016-2017/Catalog/Courses/BIO-Biology/200/BIO-221L',
        'http://smartcatalog.co/en/Catalogs/Occidental-College/2016-2017/Catalog/Courses/CSLC-Comparative-Studies-in-Literature-and-Culture/CLAS-Classical-Studies/200/CLAS-200',
        'http://smartcatalog.co/en/Catalogs/Occidental-College/2016-2017/Catalog/Courses/AMST-American-Studies/200/AMST-295',
        'http://smartcatalog.co/en/Catalogs/Occidental-College/2016-2017/Catalog/Courses/ARTH-Art-History-Visual-Art-Art-History/200/ARTH-283',
        'http://smartcatalog.co/en/Catalogs/Occidental-College/2016-2017/Catalog/Courses/BIO-Biology/300/BIO-320',
        'http://smartcatalog.co/en/Catalogs/Occidental-College/2016-2017/Catalog/Courses/BIO-Biology/300/BIO-336',
        'http://smartcatalog.co/en/Catalogs/Occidental-College/2016-2017/Catalog/Courses/GERM-German/300/GERM-370',
    ]
    session = create_session()
    for course_url in courses:
        print(course_url)
        extract_course_info(session, course_url)
    session.commit()


def main(year):
    catalog_soup = get_soup_from_URL(get_year_URL(year))
    session = create_session()
    visited_urls = set()
    for dept_link_soup in catalog_soup.select('.sc-child-item-links li a'):
        dept_soup = get_soup_from_URL(urljoin(BASE_URL, dept_link_soup['href']))
        for course_link_soup in dept_soup.select('#main ul li a'):
            course_url = urljoin(BASE_URL, course_link_soup['href'])
            if course_url in visited_urls:
                continue
            visited_urls.add(course_url)
            print(course_url)
            extract_course_info(session, course_url)
    session.commit()


if __name__ == '__main__':
    main(2017)
    #test()
