#!/usr/bin/env python3

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from models import create_session, get_or_create
from models import Department, Course, CourseInfo

BASE_URL = 'http://smartcatalog.co/Catalogs/Occidental-College/2016-2017/Catalog/Courses/'

def extract_text(*soups):
    text = []
    for soup in soups:
        if hasattr(soup, 'descendants'):
            for desc in soup.descendants:
                if not hasattr(desc, 'contents'):
                    if desc:
                        text.append(desc)
        else:
            text.append(soup)
    return re.sub(r'\s\+', ' ', ''.join(text).strip())

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

def extract_course_info(session, url):
    if not is_valid_url(url):
        return
    course_soup = get_soup_from_URL(url)
    contents_soup = course_soup.select('#main')[0]
    contents = str(contents_soup)
    sections = []
    last_pos = 0
    for match in re.finditer('<h[1-6]>', contents.lower()):
        section_soup = BeautifulSoup(contents[last_pos:match.start()], 'html.parser')
        if section_soup.get_text().strip():
            sections.append(section_soup)
        last_pos = match.start()
    sections.append(BeautifulSoup(contents[last_pos:], 'html.parser'))
    dept, number = sections[0].get_text().strip().split(' ')[:2]
    department = get_or_create(session, Department, code=dept)
    for number in re.sub('[/-]', ' ', number).split():
        course = get_or_create(session, Course, department=department, number=number, number_int=int(re.sub('[^0-9]', '', number)))
        description = '\n'.join(extract_text(child) for child in sections[0].contents[1:]).strip()
        if not description:
            description = None
        prerequisites = None
        corequisites = None
        parsed_prerequisites = None
        for section_soup in sections[1:]:
            children = [tag for tag in section_soup.contents if hasattr(tag, 'strings') or tag.strip()]
            if len(children) >= 2:
                #key = re.sub(r'\s+', ' ', ' '.join(children[0].strings).strip())
                key = re.sub(r'\s+', ' ', children[0].get_text().strip())
                if key == 'Prerequisite':
                    prerequisites = extract_text(*children[1:])
                elif key == 'Corequisite':
                    corequisites = extract_text(*children[1:])
        course_info = session.query(CourseInfo).filter(CourseInfo.course_id == course.id).first()
        if course_info:
            if is_preferred_url(course_info.url):
                continue
            elif is_preferred_url(url):
                course_info.url = url
        else:
            course_info = get_or_create(session, CourseInfo, course_id=course.id, url=url)
        course_info.description = description
        course_info.prerequisites = prerequisites
        course_info.corequisites = corequisites
        course_info.parsed_prerequisites = parsed_prerequisites

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
        extract_course_info(session, course_url)
    session.commit()

def main(year):
    catalog_soup = get_soup_from_URL(get_year_URL(year))
    session = create_session()
    visited_urls = set()
    for dept_link_soup in catalog_soup.select('.sc-child-item-links li a'):
        dept_soup = get_soup_from_URL(urljoin(BASE_URL, dept_link_soup['href']))
        for course_link_soup in dept_soup.select('#main ul li a'):
            text = extract_text(course_link_soup)
            if ' ' not in text:
                continue
            split = [s.strip() for s in text.split(' ', maxsplit=2)]
            assert len(split) == 3, 'Cannot split "{}" into three'.format(text)
            course_url = urljoin(BASE_URL, course_link_soup['href'])
            if course_url in visited_urls:
                continue
            visited_urls.add(course_url)
            extract_course_info(session, course_url)
    session.commit()

if __name__ == '__main__':
    main(2017)
    #test()
