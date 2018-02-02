#!/usr/bin/env python3

from models import create_session, Base, Semester, Building, Core, Department
from update import update_db

from sqlalchemy import create_engine

CORES = [
    ['CPAF', 'Core Africa and The Middle East',],
    ['CPAS', 'Core Central/South/East Asia',],
    ['CPEU', 'Core Europe',],
    ['CPFA', 'Core Fine Arts',],
    ['CFAP', 'Core Fine Arts Partial',],
    ['CPGC', 'Core Global Connections',],
    ['CPIC', 'Core Intercultural',],
    ['CPLS', 'Core Laboratory Science',],
    ['CPLA', 'Core Latin America',],
    ['CMSP', 'Core Math/Science Partial',],
    ['CPMS', 'Core Mathematics/Science',],
    ['CPPE', 'Core Pre-1800',],
    ['CPRF', 'Core Regional Focus',],
    ['CPUS', 'Core United States',],
    ['CPUD', 'Core United States Diversity',],
    ['CUDP', 'Core United States Diversity Partial',],
    ['CICP', 'Core Program (obsolete)',],
    ['CUSP', 'Core United States (obsolete)',],
    ['CAFP', 'Core Africa (obsolete)',],
]

BUILDINGS = [
    ['AGYM', 'Alumni Gym',],
    ['BERKUS', 'Berkus Hall (Rangeview)',],
    ['BIOS', 'Bioscience Building',],
    ['BIRD', 'Bird Hillside Theater',],
    ['BOOTH', 'Booth Hall',],
    ['COONS', 'Arthur G. Coons Administrative Building (AGC)',],
    ['CULLEY', 'Culley Athletic Facility',],
    ['FM', 'FIXME',],
    ['FOWLER', 'Fowler Hall',],
    ['HERR', 'Herrick Chapel',],
    ['HINCH', 'Hinchliffe Hall',],
    ['HSC', 'Hameetman Science Center',],
    ['JOHN', 'Johnson Hall',],
    ['JOHN N', 'Johnson Hall',],
    ['JSC', 'Johnson Student Center',],
    ['KECK', 'Keck Theater',],
    ['LIB', 'Clapp Library',],
    ['MOORE', 'Moore Laboratory of Zoology',],
    ['MOSHER', 'Norris/Mosher Hall',],
    ['MULLIN', 'Mullin Studio and Art Gallery',],
    ['NORRIS', 'Norris/Mosher Hall',],
    ['RANGEV', 'Berkus Hall (Rangeview)',],
    ['RUSH', 'Rush Gymnasium',],
    ['SWAN', 'Swan Hall',],
    ['SWAN N', 'Swan Hall',],
    ['SWAN S', 'Swan Hall',],
    ['TENNIS', 'Tennis Courts',],
    ['THORNE', 'Thorne Hall',],
    ['TREE', 'Bird Hillside Theater',],
    ['UEPI', 'Urban and Environmental Policy Institute',],
    ['WEIN', 'Weingart Center',],
]

DEPARTMENTS = [
    ['ABAR', 'Occidental-in-Argentina',],
    ['ABAS', 'Occidental-in-Austria',],
    ['ABAU', 'Occidental-in-Australia',],
    ['ABBO', 'Occidental-in-Bolivia',],
    ['ABBR', 'Occidental-in-Brazil',],
    ['ABBW', 'Occidental-in-Botswana',],
    ['ABCH', 'Occidental-in-China',],
    ['ABCI', 'Occidental-in-Chile',],
    ['ABCR', 'Occidental-in-Costa Rica',],
    ['ABCZ', 'Occidental-in-the-Czech Republic',],
    ['ABDE', 'Occidental-in-Denmark',],
    ['ABDR', 'Occidental-in-the-Dominican Republic',],
    ['ABEC', 'Occidental-in-the-Ecuador',],
    ['ABEN', 'Occidental-in-the-England',],
    ['ABFR', 'Occidental-in-France',],
    ['ABGE', 'Occidental-in-Germany',],
    ['ABGH', 'Occidental-in-Ghana',],
    ['ABGR', 'Occidental-in-Greece',],
    ['ABHU', 'Occidental-in-Hungary',],
    ['ABIC', 'Occidental-in-Iceland',],
    ['ABID', 'Occidental-in-Indonesia',],
    ['ABIN', 'Occidental-in-India',],
    ['ABIR', 'Occidental-in-Ireland',],
    ['ABIT', 'Occidental-in-Italy',],
    ['ABJA', 'Occidental-in-Japan',],
    ['ABJO', 'Occidental-in-Jordan',],
    ['ABMO', 'Occidental-in-Morocco',],
    ['ABNA', 'Occidental-in-the-Netherlands Antilles',],
    ['ABNE', 'Occidental-in-Nepal',],
    ['ABNI', 'Occidental-in-Nicaragua',],
    ['ABNT', 'Occidental-in-The Netherlands',],
    ['ABNZ', 'Occidental-in-New Zealand',],
    ['ABPE', 'Occidental-in-Peru',],
    ['ABPL', 'Occidental-in-Portugal',],
    ['ABRU', 'Occidental-in-Russia',],
    ['ABSA', 'Occidental-in-South Africa',],
    ['ABSE', 'Occidental-in-Senegal',],
    ['ABSK', 'Occidental-in-South Korea',],
    ['ABSM', 'Occidental-in-Samoa',],
    ['ABSN', 'Occidental-in-Sweden',],
    ['ABSP', 'Occidental-in-Spain',],
    ['ABSR', 'Occidental-in-Serbia',],
    ['ABSW', 'Occidental-in-Switzerland',],
    ['ABTA', 'Occidental-in-Tanzania',],
    ['ABTH', 'Occidental-in-Thailand',],
    ['ABTN', 'Occidental-in-Taiwan',],
    ['ABTS', 'Occidental-in-Tunisia',],
    ['ABUA', 'Occidental-in-the-United Arab Emirates',],
    ['ABUK', 'Occidental-in-the-United Kingdom',],
    ['ABVN', 'Occidental-in-the-Vietnam',],
    ['AMST', 'American Studies',],
    ['ARAB', 'Arabic',],
    ['ARTH', 'Art History and Visual Arts/Art History',],
    ['ARTM', 'Art History and Visual Arts/Media Arts and Culture',],
    ['ARTS', 'Art History and Visual Arts/Studio Art',],
    ['BICH', 'Biochemistry',],
    ['BIO', 'Biology',],
    ['CHEM', 'Chemistry',],
    ['CHIN', 'Chinese',],
    ['CLAS', 'Classical Studies',],
    ['COGS', 'Cognitive Science',],
    ['COMP', 'Computer Science',],
    ['CSLC', 'Comparative Studies in Literature and Culture',],
    ['CSP', 'Cultural Studies Program',],
    ['CTSJ', 'Critical Theory and Social Justice',],
    ['DWA', 'Diplomacy and World Affairs',],
    ['EASN', 'East Asian Studies'],
    ['EALC', 'East Asian Languages and Culture',],
    ['ECLS', 'English and Comparative Literary Studies',],
    ['ECON', 'Economics',],
    ['EDUC', 'Education',],
    ['ENGL', 'English',],
    ['ENWR', 'English Writing',],
    ['FREN', 'French',],
    ['GEO', 'Geology',],
    ['GERM', 'German',],
    ['GRK', 'Greek',],
    ['HIST', 'History',],
    ['ITAL', 'Italian',],
    ['JAPN', 'Japanese',],
    ['KINE', 'Kinesiology',],
    ['LANG', 'Language',],
    ['LATN', 'Latin',],
    ['LING', 'Linguistics',],
    ['LLAS', 'Latino/a and Latin American Studies',],
    ['MAC', 'Media Arts and Culture',],
    ['MATH', 'Mathematics',],
    ['MUSA', 'Music Applied Study',],
    ['MUSC', 'Music',],
    ['OXAB', 'Study Abroad',],
    ['PHAC', 'Physical Activities',],
    ['PHIL', 'Philosophy',],
    ['PHYS', 'Physics',],
    ['POLS', 'Politics',],
    ['PSYC', 'Psychology',],
    ['RELS', 'Religious Studies',],
    ['RUSN', 'Russian',],
    ['SOC', 'Sociology',],
    ['SPAN', 'Spanish and French Studies',],
    ['THEA', 'Theater',],
    ['UEP', 'Urban and Environmental Policy',],
    ['WRD', 'Writing and Rhetoric',],
]


def main(filename):
    engine = create_engine('sqlite:///{}'.format(filename))
    Base.metadata.create_all(engine)
    session = create_session(engine)
    for code, name in CORES:
        session.add(Core(code=code, name=name))
    for code, name in BUILDINGS:
        session.add(Building(code=code, name=name))
    for code, name in DEPARTMENTS:
        session.add(Department(code=code, name=name))
    session.commit()
    for year in range(2010, 2019):
        for season in range(1, 4):
            season = '{:02d}'.format(season)
            semester_code = str(year) + season
            year, season = Semester.code_to_season(semester_code)
            print(year, season)
            session.add(Semester(year=year, season=season))
            try:
                update_db(semester_code, session)
            except ValueError:
                pass


if __name__ == '__main__':
    main('new.db')
