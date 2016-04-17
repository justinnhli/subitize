#!/usr/bin/env python3

from argparse import ArgumentParser
from csv import reader as csv_reader, QUOTE_NONE
from datetime import datetime
from functools import total_ordering
from os.path import dirname, join as join_path, realpath

DATA_FILE = join_path(dirname(realpath(__file__)), 'counts.tsv')

DAY_ABBRS = {
    'monday': 'M',
    'tuesday': 'T',
    'wednesday': 'W',
    'thursday': 'R',
    'friday': 'F',
}

CORE_ABBRS = {
    'CPAF': 'Core Africa and The Middle East',
    'CPAS': 'Core Central/South/East Asia',
    'CPEU': 'Core Europe',
    'CPFA': 'Core Fine Arts',
    'CFAP': 'Core Fine Arts Partial',
    'CPGC': 'Core Global Connections',
    'CPIC': 'Core Intercultural',
    'CPLS': 'Core Laboratory Science',
    'CPLA': 'Core Latin America',
    'CMSP': 'Core Math/Science Partial',
    'CPMS': 'Core Mathematics/Science',
    'CPPE': 'Core Pre-1800',
    'CPRF': 'Core Regional Focus',
    'CPUS': 'Core United States',
    'CPUD': 'Core United States Diversity',
}

DEPARTMENT_ABBRS = {
    'ABAR': 'Occidental-in-Argentina',
    'ABAS': 'Occidental-in-Austria',
    'ABAU': 'Occidental-in-Australia',
    'ABBO': 'Occidental-in-Bolivia',
    'ABBR': 'Occidental-in-Brazil',
    'ABBW': 'Occidental-in-Botswana',
    'ABCH': 'Occidental-in-China',
    'ABCI': 'Occidental-in-Chile',
    'ABCR': 'Occidental-in-Costa Rica',
    'ABCZ': 'Occidental-in-the-Czech Republic',
    'ABDE': 'Occidental-in-Denmark',
    'ABDR': 'Occidental-in-the-Dominican Republic',
    'ABFR': 'Occidental-in-France',
    'ABGE': 'Occidental-in-Germany',
    'ABHU': 'Occidental-in-Hungary',
    'ABIC': 'Occidental-in-Iceland',
    'ABID': 'Occidental-in-Indonesia',
    'ABIN': 'Occidental-in-India',
    'ABIR': 'Occidental-in-Ireland',
    'ABIT': 'Occidental-in-Italy',
    'ABJA': 'Occidental-in-Japan',
    'ABJO': 'Occidental-in-Jordan',
    'ABMO': 'Occidental-in-Morocco',
    'ABNA': 'Occidental-in-the-Netherlands Antilles',
    'ABNI': 'Occidental-in-Nicaragua',
    'ABNT': 'Occidental-in-the-Netherlands',
    'ABNZ': 'Occidental-in-New Zealand',
    'ABPE': 'Occidental-in-Peru',
    'ABRU': 'Occidental-in-Russia',
    'ABSA': 'Occidental-in-South Africa',
    'ABSE': 'Occidental-in-Senegal',
    'ABSM': 'Occidental-in-Samoa',
    'ABSN': 'Occidental-in-Sweden',
    'ABSP': 'Occidental-in-Spain',
    'ABSW': 'Occidental-in-Switzerland',
    'ABTN': 'Occidental-in-Taiwan',
    'ABUA': 'Occidental-in-the-United Arab Emirates',
    'ABUK': 'Occidental-in-the-United Kingdom',
    'AMST': 'American Studies',
    'ARAB': 'Arabic',
    'ARTH': 'Art History and Visual Arts/Art History',
    'ARTM': 'Art History and Visual Arts/Media Arts and Culture',
    'ARTS': 'Art History and Visual Arts/Studio Art',
    'BICH': 'Biochemistry',
    'BIO': 'Biology',
    'CHEM': 'Chemistry',
    'CHIN': 'Chinese',
    'CLAS': 'Classical Studies',
    'COGS': 'Cognitive Science',
    'COMP': 'Computer Science',
    'CSLC': 'Comparative Studies in Literature and Culture',
    'CSP': 'Cultural Studies Program',
    'CTSJ': 'Critical Theory and Social Justice',
    'DWA': 'Diplomacy and World Affairs',
    'ECLS': 'English and Comparative Literary Studies',
    'ECON': 'Economics',
    'EDUC': 'Education',
    'ENGL': 'English',
    'ENWR': 'English Writing',
    'FREN': 'French',
    'GEO': 'Geology',
    'GERM': 'German',
    'GRK': 'Greek',
    'HIST': 'History',
    'ITAL': 'Italian',
    'JAPN': 'Japanese',
    'KINE': 'Kinesiology',
    'LANG': 'Language',
    'LATN': 'Latin',
    'LING': 'Linguistics',
    'LLAS': 'Latino/a and Latin American Studies',
    'MATH': 'Mathematics',
    'MUSA': 'Music Applied Study',
    'MUSC': 'Music',
    'PHAC': 'Physical Activities',
    'PHIL': 'Philosophy',
    'PHYS': 'Physics',
    'POLS': 'Politics',
    'PSYC': 'Psychology',
    'RELS': 'Religious Studies',
    'RUSN': 'Russian',
    'SOC': 'Sociology',
    'SPAN': 'Spanish and French Studies',
    'THEA': 'Theater',
    'UEP': 'Urban and Environmental Policy',
    'WRD': 'Writing and Rhetoric',
}

class Meeting:
    def __init__(self, time, days, location):
        if time != 'Time-TBD':
            start_time, end_time = time.upper().split('-')
            self.start_time = datetime.strptime(start_time, '%I:%M%p')
            self.end_time = datetime.strptime(end_time, '%I:%M%p')
        else:
            self.start_time = None
            self.end_time = None
        if days != 'Days-TBD':
            self.days = days
        else:
            self.days = None
        if location != 'Bldg-TBD':
            self.location = location
        else:
            self.location = None
    def __str__(self):
        if self.start_time is None:
            time = 'Time-TBD'
        else:
            time = '{}-{}'.format(self.start_time.strftime('%I:%M%p').lower(), self.end_time.strftime('%I:%M%p').lower())
        if self.days is None:
            days = 'Days-TBD'
        else:
            days = self.days
        if self.location is None:
            location = 'Bldg-TBD'
        else:
            location = self.location
        return ' '.join((time, days, location))
    @staticmethod
    def from_string(s):
        return Meeting(*s.split(' ', maxsplit=2))

@total_ordering
class Offering:
    def __init__(self, year, season, department, number, section, title, units, instructors, meetings, core, seats, enrolled, reserved, reserved_open, waitlisted):
        self.year = year
        self.season = season
        self.semester = to_semester(year, season)
        self.department = department
        self.number = number
        self.section = section
        self.title = title
        self.units = units
        self.instructors = instructors
        self.meetings = meetings
        self.core = core
        self.seats = seats
        self.enrolled = enrolled
        self.reserved = reserved
        self.reserved_open = reserved_open
        self.waitlisted = waitlisted
    def to_tsv_row(self):
        values = []
        values.append(self.year)
        values.append(self.season)
        values.append(self.department)
        values.append(self.number)
        values.append(self.section)
        values.append(self.title)
        values.append(self.units)
        values.append('; '.join(self.instructors))
        values.append('; '.join(str(meeting) for meeting in self.meetings))
        values.append('; '.join(sorted(self.core)))
        values.append(self.seats)
        values.append(self.enrolled)
        values.append(self.reserved)
        values.append(self.reserved_open)
        values.append(self.waitlisted)
        return '\t'.join(values)
    def __lt__(self, other):
        return (self.semester, self.department, self.number, self.section) < (other.semester, other.department, other.number, other.section)
    def __str__(self):
        values = []
        values.append(self.year)
        values.append(self.season)
        values.append(self.department)
        values.append(self.number)
        values.append(self.section)
        values.append(self.title)
        values.append(self.units)
        values.append('; '.join(sorted(self.instructors)))
        values.append('; '.join(str(meeting) for meeting in self.meetings))
        if any(self.core):
            values.append('; '.join(sorted(self.core)))
        else:
            values.append('N/A')
        values.append(self.seats)
        values.append(self.enrolled)
        values.append(self.reserved)
        values.append(self.reserved_open)
        values.append(self.waitlisted)
        return '\t'.join(values)

def _extract_text(soup):
    text = []
    for desc in soup.descendants:
        if not hasattr(desc, 'contents'):
            if desc.strip():
                text.append(desc.strip())
    return ''.join(text).strip()

def _request_counts(semester):
    import requests
    url = 'http://counts.oxy.edu/'
    headers = {
        'Host':'counts.oxy.edu',
        'User-Agent':'Mozilla/5.0 (X11; Linux i686; rv:42.0) Gecko/20100101 Firefox/42.0',
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language':'en-US,en;q=0.5',
        'X-Requested-With':'XMLHttpRequest',
        'X-MicrosoftAjax':'Delta=true',
        'Cache-Control':'no-cache',
        'Content-Type':'application/x-www-form-urlencoded; charset=utf-8',
        'Referer':'http://counts.oxy.edu/',
        'Connection':'keep-alive',
        'Pragma':'no-cache',
    }
    data = '&'.join('{}={}'.format(k, v) for k, v in {
        'ScriptManager1':'pageUpdatePanel%7CtabContainer%24TabPanel3%24btnAdvGo',
        'ScriptManager1_HiddenField':'%3B%3BAjaxControlToolkit%2C%20Version%3D1.0.10920.32880%2C%20Culture%3Dneutral%2C%20PublicKeyToken%3D28f01b0e84b6d53e%3Aen-US%3A816bbca1-959d-46fd-928f-6347d6f2c9c3%3Ae2e86ef9%3A1df13a87%3Aee0a475d%3Ac4c00916%3A9ea3f0e2%3A9e8e87e9%3A4c9865be%3Aa6a5a927%3B',
        'tabContainer%24TabPanel1%24ddlSemesters':semester,
        'tabContainer%24TabPanel1%24ddlSubjects':'',
        'tabContainer%24TabPanel1%24txtCrseNum':'',
        'tabContainer%24TabPanel2%24ddlCoreTerms':'201002',
        'tabContainer%24TabPanel2%24ddlCoreAreas':'CPFA',
        'tabContainer%24TabPanel2%24ddlCoreSubj':'AMST',
        'tabContainer%24TabPanel3%24ddlAdvTerms':semester,
        'tabContainer%24TabPanel3%24ddlAdvSubj':'',
        'tabContainer%24TabPanel3%24ddlAdvInstructors':'',
        'tabContainer%24TabPanel3%24ddlAdvTimes':'',
        'tabContainer%24TabPanel3%24ddlAdvDays':'',
        'tabContainer%24TabPanel4%24ddlCRNTerms':'201002',
        'tabContainer%24TabPanel4%24txtCRN':'',
        'tabContainer%24TabPanel3%24btnAdvGo':'Go',
        '__EVENTTARGET':'',
        '__EVENTARGUMENT':'',
        '__LASTFOCUS':'',
        '__VIEWSTATEGENERATOR':'CA0B0334',
        '__VIEWSTATEENCRYPTED':'',
        '__AjaxControlToolkitCalendarCssLoaded':'',
        'tabContainer_ClientState':'%7B%22ActiveTabIndex%22%3A2%2C%22TabState%22%3A%5Btrue%2Ctrue%2Ctrue%2Ctrue%5D%7D',
        '__ASYNCPOST':'true',
        '__VIEWSTATE':'YHW6rlJdnJ5zFgNO3XH35DrK76Y2m8eTsE39L2KUJA5k%2FPGXT3%2Fg70aMtjBOd9XoE5FZuPusE8EgohnrzWoOSSfg1fa%2FptE2BcgwAYp4JkKleIMPWRyiGaUL1VYuHHCB7YQTKT8aOuXUqWPmZO57f2z1jt1tSwUGa8tcF41MYvRtyZ%2BGj5w48A%2B%2FaTbj%2F%2BxZO4UDThC%2BQzhOqOga2wqDKRRuwrC4dlCV1fJbBlMQYrMZkX2cV%2FczeuMWBK5rE%2BgBnLGbCXXGBRLUOzQoPfVyMabVx0VN22rqJNGUxh9TuXWRTUE8%2Fwy%2FVHgQdhng0FOK%2FbAnpy8TAHv1aZyEdK0EUGiDGFJ6KXlWxyZGDdeYxpyEYeJgrG9MGeXuWN5dO36NPAdJZV%2BSPPbSqFAM8swhtnrNWvqxn6sEFJeYOGSzhaGKqhm6ejw0Bt9gjkn6rTuXS5lR%2BRHr3Dy%2FS6gwTttBY1Uap8UX7oG5uIMUX%2B%2B%2FYaOVyWG8EhHda4%2B9znNkqsh1hiifVX3rLyi8mcx3%2BxQvbgHMkKYgIlPMvwgC3sbhMaovdewTWl8Q%2BqkKvoHFUKy58FjGmbsBuohRAClLX1EESYJUIBRREdZPljoF1M2tXEJxAi9c1rmIN0DuCL8b8CaDTcGMXKt1o6U2xkvAJtR8YJFOSZuswdXT3EfoTWI0RjuNh40G3YDhRIjya%2Bl7RfG3ps6ZXmfVZzD%2FFBet2ly7oB05oVXZIG0i5ohvzNdgqnISOR5GWnomT4Rv6oCE6wNGtXT3owDjW7qPXidP0mXdseSYwfa%2BcSQHt02qOL54dRnyTuY4BYNCgb%2BkTd39o%2BETqadMBJ9QSy%2BM1Wgdid4T4hhmQD3XD2ucnWe7A5TDpG72%2BDDfEAOECW1dECvpsPIqUzv2hZpb2zrmyZO4UUaSd8o9A1mlogitlVbXT%2Bn3DObN181SMtJjLiVMg1qw31ltLs%2BDWESJM6jou76t6Kajq6dt%2Fi0ydsygbxdnpnxOLGmBn%2FCZoJPSoPXO6GSNp%2BUE7G4MID%2FzapY9t%2F%2BeoEbPn7FxEGd%2FzQAqXVHnbzUtNCQhqVFhPDGsMmU1cmacUHuNKF9bW2CBhbLJNkvYRUOC7hcj7dcZreN4VF%2BkiTsbIXYSU%2B7VYbTkjXNwranqPTSkJM8bz5wVxPtBx%2FOVuCCpA9au3R0ts8vJSMXgiPjZcTNCunieE%2BEMTkLCiTcrtazYvimbl2naTo08iCVS4K9JPKsm0HSrAdEUbyeFJVHSd%2B5fDNGns86jS5tgvXLYkZgtNhwLpEjvNP5GJXOQJ5tXqv6ethYyY%2Bpc6%2BTucLO%2F%2BWGk1eys8BlbOujypwubgDhxurv7g7C%2FlkDF%2FVtjlZRDBeiw34MGrf%2Bd2h8FucMex2NvsNSVuWzOnSlIAeIElmSkDxEF2BDziwL1AvL2mO6RsZ2WJo%2Byxo%2FFNfBjmKLTCmzlqxC%2F5UEXGQJ%2BeVVwoD1nA2jRkdLxh6GDp2qUG4Sok8jw2J6y2rkffvLxG2kaezDFRwfgl1DqBbWOi%2B37c4ES%2Bu7lh4Y9NbMMuaaZwblhZO2eK7OZdqI5wezJSF8YJhA%2BYdqFUd%2BdLphKdvLFm%2BC%2FZNOZIXZI1zzxGpLKn1UnLtXBd18jtwlnVAsbRxgdg0hKbdvihvnzGOKFQzlmvdoIoo2IXFZHOP9jpxak1DDGovTlbkr%2BFUckA6%2FEopDyxz310EZMrnJiu7qYHMuxuslt4sKpnAVVpC%2F9y%2FAthx6AKF8ePZGafhdlVHEKfUafKOtCmXtnhJZHKPot67vEH%2B1sZPhB41zJ4RUO2PbTPbQstSiwJSpUHWFD4WGoVvCRjv2BsEw1TLVY9dpEgFSghwpaqzGhzXJcIHQKOj6UcotEvh3PWP%2Bi2TAW4a5nBVhmrAmC9lWIRx4j5mWgc7vjyRu%2F56qwNC5P4JPaHEIDE%2FrU0JDQ2Teq%2BA8FiRn3cyPCgngvJq9RN3YUwS538fFzkhrcu%2FOFI68JNZsUITTK9pLNOOW83aG7d5FqF%2B%2Fq7ZJDDTwwpLXjxHpYQ7Z5v%2BQN9zLcMq528sThpOPcaKLKWVYZ4jmadTT%2BFarD91YCaf3z1oa8itcKHtnuPmNFrNCzyntGLhY3MKhs6Efti19yPekGtGRyFfuhReUaXRBDU9LGLH9qG1oavvra1LL2SRQ0HYdlCUqjzbNOggYNWYPO%2Blbbjnezvopmwiw2gDBZwGpJmT1wGD6y%2F80yy0Ti%2BZ7Iff8x7d7RwGFv%2Be7MrazqUOxyojfie7iK9AtrrocN5RorYR8GCBR6N11vdpyfeb7bhLSj5YUKXPfSgCmHGDznlIKgAe7e60NReIU%2F0kz5DjUpbJVkQXYWt2QbSOp61TSWXPo6CIzJHDuJ4Xah2NzNv%2BwWPXbZkJ8%2F6Ri09A8iRdrQ2iq%2FkMVsG0Un1OhXKX8t8CArbX1MDconjUjvpBtDboGyNSsrm%2F2VyxO%2FUO13JFcJw0kalvY3eOEkENYm061FOuxsP0eWElTn6EgjIDVyYRn1NcP%2B3Xxw0LqNL839DkNJE0%2FZJRGMuL0ls0InYT6jqHAMqYWUHHTa5iltQlGKnVevk6c5om%2BtGbDlOjjrkYVHXCl661LaTX8H3hY1wZTrfH%2FAJNal5dkeKEJnJD3ujGbGWBC5u0vHvH5HBnECa4%2BQjgk5cdqXRc1XdBaKoFGY8qxXslNGH3WYuqjHOLpK2srPS59TFtRt7u3kdOnfx6PQdvDYylhsqXfrJ7rq2%2BfvUlVMXUjVHKJRjcHzOBNHaFvPQefkHbG3kmrk%2BcUnTsNC9X8pf1g3DC8j%2FRYriu55gH5UFCgtba91bczmbWbZzGmwkTZsauwHyYJT8UtwrsF9JBhn5VovODOhu2ufwYj701QBIAmkzvUWtzwruwkXTsiV%2FDMwL9d4UfsXjZGpUugrm3HfTE%2B06MyMYxEQFqz4zoTtiDimCe8u0o4o61HslyHaWbYhSgiQVXTqTBfnkBJJmgEdPKSU%2FtlKBVCjVb5aqBLk9nwbYRd4kfq3YMPcNTnTHuNgQ5FOGGadB0MACvDe1h9nD5w8gvZdtqWODCQPiG3FbUcnWs5FCEJN80VYIc%2BneBuhECm%2BoDjAT8%2FkTQzA2sK3tlt22eaJ8MiCukzF3jrHVBTMqYAuUzX8%2Bc5c1ZZ0Gm%2B6GWnj4oP6Tjuj8HXmn9lQ4Aj2Hahq06P26AyaKbzamb73mIbZlP4roWlOweA8QbH77t8pZIZZ3W8bSKU4NDL9Pi9O2jUTBz612SR0J30sq9l92ughvVKHH44ByMsE1wJS33XaR6kf0a2rkjW29bgrOAIeOMKRGnxnXL4Z1GoGDGbpZS5fS2BNpNQavT1rQFJ8zH%2B%2FAdz1umBu7w%2F0sGpHdwjPFNjNvZfCY2hcSS%2BHshIKy8iZaoIbP37TXbkQVycpZuQ1s7a5b4V9%2F7NpnAX0z8sJKj23EKSFHtJ7JkfSqO4HeXDJ5WuE8JFIao4Bw8k4gwI55wZJ6Wo%2FurRT83RJESgGHQ6439oDnHDiJPh%2BQs4MKtlGmsNCJ3VrtsqxKcli9IpycYkIqNFsMNvkO1%2F2ekBPg5Ch8V%2FtUq7KI%2FEVDQwUKzaFlq9Jur2HZ%2FPnyKaI4CNk%2F3G%2BMfgSDuWYZuztFwxvm15smUpBMDFr07KvxiDnUVDpai4Ga85%2FT5JSpC9iSryQD5fisAh5JzG1etDHw%2FuC3WEswEcohnIs0fi7vAsuLLpecVgmLBLuOdUExp1CMKXRlH0zHV2zv7I%2BWU9D7cC%2FvR4yuVTPsyFMu%2FHZN%2FNYHSjpPRi5oqd426VIEmoxk4ZeGieppXZ4syn1QKZefsB3kH%2BwgS2udQJJUWeOaaCSWGfJO1Db2h%2BONNnS1Miwcz7Pp46m1O%2FORRNxP5yu3HcWAxlN6fyzKGUjr%2B0CMHt8gTUQdb8CstPOarDtFlAOMEfc3RnSUyDGCr59fV03cIQJFumrsMAb4%2BqREBooknX4Jsii%2BZsHem07EnEVRJBl2eTxPN7pUNxIyUpw6q9pTOdKqGUykzUJiDT8BsIzKGyCarBih%2BG3PZzuBja9CZ7uvpBZG3e6QEt9wI6GPzWv%2FErMrF9ra8JmNnKD%2FfuIUX7uQxay1t8H6ViaUrclBbThxd5VUPwIs3Zde69jl2MX%2B5XCeWNLDdHDswqIlkN8AUC3kkuXCdZvfxpH6aBpsyWvewUL0yChxcGAU4SXNbP%2F4JlaRUsTXpfdaQ4rFLfPue2VTaElHybC%2Ba3p82pa4P1iki0gcyn79z%2BgYpbnbpEnuel6JVS%2FSzQDXjie%2FfUDbzpHOBMuy6RecKA2JDXPgxUzCFH5A46lgbckcQxz%2B7pAlQphM48NZ2AKFyPUYLfxE6EKi4Tf0RqI5%2FwV4GfilZl%2Buhdlocllo2fe8YKRkkwsD3C5N0w%2BlRxchPiQ%2BsdN3I8n5Vd4VW055J4wEoFHqV%2Fw6so9Efv8WCkXzZor7uMEA7udrlzH3T4DaAUgyzQf7C0gxHhdnYkTuqCFh2Ldoc8iLB2wZlU08Fv7wdbyXBdiBIhQ9F%2BSeTFD3AHy4MROW6YmFRk1mL7hbtQEFjoRO10vkeb5j6nw%2BDcI982lOHrHyYiskK5uQjePFBC4XkO4RYFzZ6GdHQGgTRkeDiy%2F2ZhP4300vqw%2FSXcJMupDMYmQUn3cqGChWTVVF215DnfbESzw9%2F9b8imWoI2iDA1o%2FzTCPfzi7X%2BdGvXE9mZobx0FlxYC37xr0BcpAe3NTJEsZPUIVOqXHu9IAh53HK48cXNDjqGu9ti3TFSCqgLlQF1V9HmtKeKYKKDcE%2FLifN2hLELNytXo3Z3YmACbJv7W918e7dnEHL3Atcy4wjFVwEwcF44YmyBV8XdXwZ%2F%2F1wPUzm4%2Fj8ukHvmbTcuDz%2Fm3wMkkzNNtwpxwAfIlAqnfPDkwfaLT4VGxeb97dEmqIhr2VqImHBfyg8YQqUyhncNjJZr0eMWRqfwPcZId5NzvHZk3h1RjTBTNlnf4xZwLiHM4IDSoCWei8OyzIUhf4c%2FMwhoi6GjME5BmraXee%2ByfkvxeA1MDQQ2C4mJbG4x4ELuPHQ9wDHkmx6rOVF1UAeDxxgzfEEewWvBrfclnG6FpHlG6u3yP92%2Betm8VrV2KfkaHPpCupJx8qIA9ZK8vD90%2F1Eb%2FyYBIvarKbNwzWyp5tSD1RnLB5S8fjLFdYkU5tOVQtU69PFzgO2KKHCKHKHnzkEF9iF%2Bp5lnT8S0GiSYtUJ%2FqhSzps%2BBudmM4JWCuVt5B16douOpHNAA9O1fmYvMutaLJGfS4dxJHeu5l4JjzvAnUbTUvuIu0U8z93Jtex5axleoJKcUcGY2gBJQC%2FZiy0%2BFsYSBmYLpr%2Bf1s07U3cgldSHyZ1SHtAw4jKJz7GcOQrbrJqFfMtKB1HzXEFi1UZV0m%2FhkuRq0e0wdAzMU28IXPWwaQF9HCrsItIj8KHnpXSnkK7HhlZeioGgsipoA2QVoErnFU4104IsQd3oxGBeuORGPEQNBvkPNuqLIMMuuMOcmZNcclTj%2Faztr22x41CQMqTgM2ubmwQgvS8tUlHjXMu3sHuAd%2BygeU0w%2Fcm%2BdQM1rzAtkkc6yShL3%2FDfqrrhAMSMWg20MskmGpytdQMQnC7yIVl2GOwiTPoqBCxaaM%2FkgvIaBWFsnwjWzvFWJOaph0%2BOt2r6X3YFzvNAs4wQbCgaC0K91WAK0DSMpL81ZAK7dKVzCgFAwHDGz858EJ1hYJ7ojTNX2qNUY%2BVdiYCJaUgyoHqtVhcvTu2kCFEVlutc1X0%2BPwvYitWpcYk5TFs8qC5YuEVC31xQ1%2FBPwFU6rn2pbAvNNIlQxKcCUGAk38zIocFm0vkaOZyj8cncyiCaUG6RaR8uSLJ3I7pafXZC2q7FafUKOyf%2FNk00NWoLL0iWU1Eb%2FCi8nEM5HcCCKMKPsGB8mjkDgTMIl4akhN7SNKKrY2fXZTippHiBNg%2B2DKavSRxVddr5JYNgkWqBbVncMTrsEdB5TDJlS5WW4HbO5N9y2kAdePcxMYO88pGPjbC7B4%2FXmPiw6r9JY%2FzgqGamj%2Fl80MHQxD7CKVzKtFTDW4oCLzJciFC1G2RxYq3KGS7OE%2FYRpRO5YL7gF4TfgzedoheP2GDXRbDpt0tNLMuVwK4ybh3ntCCM2FK%2FIaYWWFCWGCIPGTFR%2FIiKhbWbyozxMrBGQG7UxZUerSRZ%2FzzlvX8QEl2IXdd8NDaVifVnWYJ%2FWtJ%2BXdk4XDdQeWpJhm1ExTMwD2WDC2XYQI7ppDQytPoELGZhQzRy0n9At1V5mCHW4xfl3CZHy59EpPSNdtWEMuts0iyplbCddk39XyTiHadWLhjZCH1LKk%2BGNjRL5mNdpNXkWm98XQsYd1zdlSFYrfl6u1h0gPWLXHSTndJ6y%2FdFl6BKKxiKWRGRNMFGEPwG9F7UA1F7H5vF1cGpMN0AUV71zytO9uo4an8Mw2aFO%2B2CXEf6Nj5PYDY3Q%2BKL4ytw0G22ZRcVi0effZO1hBBA%2FzQh94lCCfvY49J2RsU4gMvUlYUb2LCmCCNTl3DDtHx%2FzFw%2FLXHAQXVlMDrheEQvc%2Bj7igcI8fuh7Sj1epAeinyrnfXClwanBp%2BvcSlF8ahzN%2FA8bLatx%2Fw6XGxBonqK7ty0n%2BKSyoXnqFCbo3iSm70jelNY3AXUTJZwjs0p%2BvkNTilqzpM8eeQy7m95cg%2FdMluC7nAgcGe9G5J29WqWnMhZcH8Tv6HKloEXhqo0YmHCIiq%2BH9Ms4AubQ3JsrpGVtf0XpwkdG%2B16Emitphz9%2Fc1Ce5XjRyD50etb2NUHvNZgrUFyiq87ulif0LEefOb4lASbcc8L6%2Bi4Tcpx5E8PKH%2FGnDy2DlOu%2B4NBYRaDaj6aOg2aNxrO%2FGVE3%2Fwch5z51pm835HP77OAR00VDy6srSll9h2djYqMPL5tdiJVynWCdnCJxciOOAwKn7oOjAZm95EVW5bbZeIygI8kuAa0nTV%2FV%2F3a99bXfbiZAmGUkXamIyt0gWKzTGhz%2Fi2Nxav037TUFXhJIUAVACtIw4KkgbmiycW%2BVQFFzD6FieMjb4UI9BaQsMwYeDwIJpV3arINR4nlv2iD3S5cHKdTvXfsKsTNLzZtEUSBKprNPgVkjz5z%2BsXtQbZqvbJnN00zGeIeKmW3sa%2FPyFNrwL03sNM73MaT0Q3k9RhYv%2F7gfeDtnV1cYD0OUEEXiPTki6c5766rk%2BqMXr1o40gZ%2FrFfNrB3aExitRUw1INIdGkKiIv%2FaCv1wZnju5lWxxbzvsJJzwJlSPQrRIkoPbveeYVFDfIFsXschB%2Bh5MSVXPO4HrdiBnFnFBcxGA1V7zDfJWu%2BjWi0heVV4Lf3ZOROxRJhEnMNfq%2F4C5gEQasMO%2Bdx1qvF070Z9gWf5IDrAc379I9jLjK0mg5c47ShGBxP8UotWoZJ1w6mlm5D7lLxF1jP8F%2FXLwDeI%2FJaSPSUTBowhxfs8qbaPwp71c3SRKHqAWLDTb5qQczYcJEPLYDGxZrEF%2Fqivi9TsQtivk%2F6xQq4VHHO3RUGQBFua7S4xaUUSLKRvfKx8K%2FX8SrvH5CQKIKNUPNFlh50w2AJpdFVv685PRY6QzihcCkvOAmjKgMgEOw8oFbPqTIsiADvXzD3st49gxKR2jcYRr9hMu56fkPyFG%2BPJiKwCp7S0wXkR0P7%2FRzSB77%2FG7p73SfEaQ%2BvdyvvmUTQn9blBHh8dPGSDAwQZvCM2WvPQS3sDVFBI9DIq5rbmmRxtv871fio4XIWiAaKi0i%2FMXFz2dwWdWgILhMNUXvHOnop0LRFtxReZvAGwvgMonEAFS5hIQMoPKkoFZgMAaEMnOOtLVZd1I0oCNV8pyZTgS5BJdcj8LXfYqCbFdlwzbslGrxbYw%2FBaDIRLte7SKxYsaiypyR4FpE0cPc2F2H9j0FxWN0J%2BdqawqpmfTAWDw1O71n%2Fzsds0Z2MZuW3c9AOpcrn5pGpcXVDPQs923AkiPeNZVqBcR%2BEXLtHyYWZ%2BNU48KbrBrSCaj4Ijm3LilrpDk42HYCpov9ocBx5KB3P9lhgYQOvcQZCT2Bn%2BsWzLudP9UkGX%2B0u%2FmR%2FkwnYt4jMJeiHLclWPaHvSI7rmWTuA%2BfhF%2F1T8BYZWFGMbagpc2bf2AIqkxO3nROteX7TCMsVjC%2BcAe6TDTgvgZ1bcTqgFm79hSouV4ZxXjCGWPVcr%2Fjbcd15qOEYXlIcr3qgGxwE7K4BvhSz3164SVldAU25Ok4KS6ArDmTwhOCy%2Bn7sq0imOx323GRy%2FGjJ7zSkys5M5Q3vGWqojctmw78W1ZCFBrVOHOv7P0muM99cYf2wPaLuKJGSd8fVH350kmgS1RhnypHZOsSVYvOMpGHsk%2Fek%2FEUhbbYSM4%2Bs7iNqwtTwHJqN5zIDJaRbecthCicelQSxZAfEcXoNtnaiuKtQqyhPrWSOfjGjRxf9LWolrmvr%2BJP8uiKRsS%2BU4xNLLroIVRwqJfp2yMI6bo58npm%2BaGJgb5s%2FefLWTsHoLzGYkUqCURaO8MOtuAE21uxcGyIe2gt%2B8zveC6eaieuGwrrRNKso7fUZN0MSqN%2Fm1N6WXJGtlhd%2Bh0tX4FMm8WCSzD38TqMHkmtRk8Su7qvJwWIIiPFr2FNv7%2F4VAhJ0JSxAxq7p57JhEROcNM8H0ImAjLo%2BB%2B4qZt6X%2Fo2bKE9SRWhF0rLSGWgOKFMoLex9VaflLK7KoQJIrylJAp7m2cTUyX3YXxMV6Os7S6nW0DSsHO9FH5Jo6cRueTQexvAmsrlKIjdP5GLnODVUi%2Fe3K%2B6JHx8a%2BqO%2B7z5F6UU31YCsm7kEJLVutKXDDaWuqgTI%2F1fPqMDJDIGSv%2FvfnwBLQtMsUh7iJOQcX7sC2Lmci%2BKs8VoVtk%2FqSSg251OJ5vgPf9QjdjSAOMONimGTY01K0HcfGGrdWzOPYLoQu%2B5gUSGxhk3x1j0QflVhUcIuF19KKy9GfT4gM2D4jaktqte7%2BrqdIViIi%2Fbs1qcQwvllE9YLz66LO7D5t%2B8MZ4SiOiU4SnsyI7ko4CTYsQgVjGVCUpxN92itXbmOTMQfXNf0NQmTple%2FUfmjh5sE2mZ527x2YJ7jwsgSHWPZi8DvZb682bL3HUFuyxKFF8Gd1WlDxZQiZd9nxVbzNUdZuhajPLz57BYS%2B6avBxitRRx5ZptDsubfKATlRlH0h2cmcX6DP6vpDP%2B7mFk%2FcP%2FXoQcH2bFlaz13rNbnp8rFHwhMXloMIacHdefb%2F5MUXvQvo4C693NMRryNw3NKOY7QyAty4I6DwgGJyKUcHcY89OM%2B3D%2BRvfx%2BgJdm67KpAtnTI26WeTBPIm3BwLybzXn0RuIB2fqhaVhw85ErDT%2B8HYgjYFqBJoIiLfUiTjZueuv8pe7FjkMUqrO%2FtBvvmtQvKylL%2FZ%2FXM8dAd6%2BMBveqjI4nRd2tCpDVOcOjOLcPq%2FTuHUUOTeJlad6HrHXmjk1oTqLand%2FNR34U4adX5hAAqgYTVXu3gp8NJgev9jxIUOlh02eyxPg9AEz9NzIMaZYQUZY8GC9GW0%2FxG%2FXlhvIj49YYzz0n06VZ0ezeqKMCSfTvHFwVGK8cfGtEHWzlSCS4H1P6SnuBPb39ixZZPXvx%2F9hCOTYdQmAdnKRlSprDC4obrF8KaDYA7K1NCpy8ODy2bYiu5hjoowvJUe8KSp7B7zaei6FkcCMD71PM%2BAYI3h78%2FOf%2F1YBy1nFfwZgkrvc92%2FB0%2BW5DSqT8LXSYqh3pUff5wK3nF%2FmHerD9zgjgntaKqNbo3VdoeA15djDuWzn3QOG9zF7yf3JA2yLJosDDqdtQkg5wZ2TQR9w%2Fx0HzgAehAjMt1xzZ8s%2BDTMRAsJgwJ70UJs%2BQFij0qBRmm0GAZFeyXfPnp6aTpsKvymqV%2BDVdqMvaz8j9Td0ykZRYnWKkirgX9QjFGTq17zO5KnaoTfeDfAMr%2BuHk8Eye88LvaOCAlzfRksDkDruCOeXSbXTzPM546JlFJ98gbTn8CcYN%2FW44AICr5hl2LYu%2FTIoKvxYXAnb8oRVP5pqwg84ucweGFY5dZPZlVUKP3Y68S2QG8663EWQUuov22Zt4pKD0kVTq0GwZAW9V5NnnDLbOPflcmKwmsH6il0eR%2FGFP9EhJ8bzzmvCGEP6CDn5IN%2B0TVo0GwTYc9UU5XWpTaYlCtsBUzGvJnLix%2F2NeZatsQ7wjyCRIx8rsauMNhsW%2Bf4bKzQVPsLloBBsiNwO%2FGw7cftjJ1D%2FXcofiu7joyzkCanImAnJGZXkV8jx2B9res1mX6rbkAcFkUEK5mHB%2FH6qbcd0ORCpBTuSMojCzMRjXvpRmpkOLQuyaZHfn5UR1EwaXhvn0UUBQb5715bGhdHU8lZ81rHXYhyjv%2B8uxaxKpiXsTV24P8XcvxZpZ4SKhaqnRgpMfEZHiox3Z6xszExtkB1uodKvwacGWecJOKbxytl4BFGuVUG0BKhoKJn1LyULXhUg%2BBwUyNsP8E1VqMI3YvnIjJQdWp4eP2tFEuJ88B7inG4LvUUEfnw4FGpQtxJZva%2FDfAfJ%2BGy%2BaQYCf2XaehyyYMjei0kCjHWDSMzGaTS2t3WY2%2BtD8Z7V%2Frqk2gZqBSl9HIbN5jdZym95G5prnBC2LbcF6UME7nU83LHdxUKoDYoMJrZAOYckYz6JpNT5kL1XaNyE6cgTwGMctLcb5CHsfT54QEk2WTHNVlRRiR%2BfV1NQYCM1xsP6hdqTTObsiTyug7hq4sIKYxLsVKhUZV1Bu0qdTAIsKmCOeywvjY7%2BvPkBQ%2F3Z0SAG8f5uEXHFc3P%2BgimzCLQZwH00zuPXtSXJWvC24mP%2F57bc1BXd4p0e94MMPQ2%2BjmDUJrIc%2Bl5fMV%2Ff8l%2BThSi8NiwMqIIOlmrj4Ly7McK4Jz7hoRnep7z%2BFdx3QS2SyMX9zYHTKGwxX1kSJdfvDe0szWSjJ7crnyKOhTfJd5JUC832f3W0JpsTTS3fuQP2m8uXGSagAzhsUDsgHV4LK7KgLcimws5KPlDZeVRD5EOah8KtbuzTffSfcwB9dkLOf3FWJBpVAh1%2FShNOvtZs6mw5o%2B1MkU5vu7ptIzucILHHWR%2BVKqQ6OAQ6cQhuUl2OLjYKN1wEZYYR3FFI%2F5qjwmQJVbBprjjA%2BEUzzI2siWfXCjnDo8DGPZ5qZ3XQN2TnEkL6y0Ka9SzfcuZ792xYFDVKZLehATEgEhPGiKqg2%2FASRCwhEqpCAqYATQ0UcwkuBRwRNZkc1vkWpYMDZJTyWvbIoQ5Yuv41xZ0WKUmdxQU1g1zwct1y7W6M7nZtmZMoCGyzPvEX01v5HlIThMrrt0w8jg%2ByFLZEybB4ZBOFq2354FkRDx42bByxzOiAiNFP9aotd7FTP7%2FVF9xmJAd19FiPtO6rxpLn1NE24J2NCGBBxqmkd4zGz8hl52DoE9IwDXF3WDhy%2B6t0%2B0V0%2FWpxMSAcCo2MEtl6rInKaz%2FRdX%2FtpTLDgJkkPlIcpVztcNL2Wo6mXKdszFdFm63gTAwfEjHtfkXAC3Le9CbVa9gJkCEuadv9YhRWUdVBIudx1h0PH%2BPSAs6Zh0ELPkRMOgPk%2Fsr2Ik3OsIRlIsl9XXtorp3U%2FN8E2406pRSVjE2i66B7BaRL9%2BTv9lgt5v4z7at1o1lLoXHeki2Uk3EHl94gycvmgxQq16WXOGk4gs0huSzdqyIzpHfa6F8WRHKxwoafA%2Bjdx2BR95zIFyQzNNWqjrqzgJyBp1FdC2ECFhVCrBFAU9ufs6HvOO6zSG0pGQT4sKSkZbtQ%2FHwefA7anny%2B%2Bz%2B%2BVnR1Ba2d3zz4%2BhLiSAEm4CHpgdlB%2FA81lV79T78q%2BTTHlcwJmEqBjawECJroMaByJtYBu%2BVOmkdFK67P8Q%2FFX%2By6CJAYxmKV5AQqvV5sKyu0xdJg1Doaa6JN6jutkz1xXoRQJqOlvwnZhEkrcE6SGmRwrhgDP9j2zSvpe5%2FPEoEqXJJQ6TeCl1kwX3GX4%2BNyO%2B50RrfeY5uHknP96ZA69imwaSdgpqON2aJ%2FdqzbuD9xuxCe90CZUwie5i8kta2WDCYqCqThzGVmcPtUTs1fEb3%2BbCSw8ihxrPwuO3oQJUBUd57H22j3LogEvUg%2BqfOLdVB1cd5e3rxQiATTkYGjeCwxeQoQ5Mq5ZdYCUgSImrCxXZw3SQ9aDdrimXSU%2BhCgzq4uLalo2KVIqnm52moS6hN4jIDkg%2FDqBKTNUNLpkXWBjYGIIljS4BJuy%2FGLJEQ8bl0btKp9F5OnOPgRoAC60MSHiBFlQl5BmAyAB9iys6Ar5vSsiwkIVQ5Vj8pUMnj5yhN4d1r6zUBHpPh3CXFJZYb8hu4HyWRiWBIDanGL7tE0MNJeZ45qKUZW0HfDUipVTjYzfkf6iboulHHBkxkD0Qq0B0UE9JtA0D5d33l09WfuN0AoZywGVeossivXCQtKarTLNsDbhu8TaXLk4uP0UAgwriFtWZsZGnVbZ7pSrSEwIDizqCoPUN%2Fmpq2HePAWwCOuUj5tFVUtM2PTpCflaMQoq4Y26PnnS9CNr8S7ebcpvCBcCHYCqvJ1WwPT717sw9QR%2BP9CO0jRr9kvtj61g2gm%2Br5v4tXK6XwJrJ6%2B%2B22Ax3fnFu0FcOgguC%2FrdcojYzQVpUQ%2BVyrszYfseN1lhYqrtGLncXZOx3sNJoxy4VmQpMdHEhIaunF0qD0hNVXqUoyZWgMot7T5OokuLzJCwttnyuTYyS%2BPIk0UIdTbYTH5DyRCWJpkhkOH%2F2Ua2ysXRRHM4HLxDWHUduqLWEiOGzIPJgPt40AGnQHWnuEDSotU4JhmqaONo45z7du0ebixj5jSizIMcp9O%2FwqUsCRINH3Tfd9%2BuwoR72aq7qzNH9VnOsJV5YuiTEQnxSuha4OlQ1jKNxuyfIzzXNTrsII1JogNkD81SWZPNqs9UnZ94%2FueAl2JsIwKA6CPsRdHIYxGqvhLUCIdWQpR0tq0uejFtLWjrEf8ldHwPa6%2BQGKTl0GiqzniMk9fBgkZ3E1d%2FV0CIfLrvdqY5uzC32%2BGPLaY4vkfc2PCouB%2F3uFLBI2OCjt5TwoR2bPE9FJKacjf5xqLBUxqdoetaZdQV68Re5PJMJdn%2B%2FjK%2BR3FLbXW6SLtm7q%2BwREUWRtK8rmLCzFxdTZSDKHL8ZdNvClmzFh89YJTvc32s2x%2FRImliw15b%2B1%2BI6TDuqoxq0lg5A1wlkdYt56gEVWANcWGhUebd2sf3SdW51fon5%2FNsLXKZKXYQLHt6U%2FsCwN21NakkXzoMRmp2C%2F5a4i7AYApf8oasWeAwLhWjoRPbhF6wGMczqkKw1s0VqGUMNooUKq2JpPjXVDW49ckB623%2BUb7fK7CHHxg%2BigErvle8Tv8n%2BeNoiutXrgKWR2J7LYP5OoU13oWL2NacymCJk79pYouEACAkwxby4lQ8kfw1LHwYSJJbb9Fpq%2FEXuXLtO8BM%2FYHMq2w6kNXyz0ap%2FL0Uw9vTMURbmQcE2UtR0gJzklUC5006807yh%2BYS1xTJjz9xYblHUy3feSccLWhyFzspy9vP1I%2BO2ch2bRj%2BtDXKThW7wFkoba8mH0R%2FAz62sp7H3DbMD7nR1KjmUVNAOcpoI7qW2baelogVgejp3SxlatDk5slEgBxk8i24YbMnGMdlVwrE6CYxfCNIvbLDG9b7stziHz0uSvsPPsGAQRE2%2BA9203B0rGK2zCXjDZ1RohgwIJpLcHTdbtYVKn1hg5zlnqJ9miVn9kDo6uKVsCGmMw0bKjujguCQeDEegMxRto3GFjM9JVm1QTCreZrrm%2BkpCswOvIEuTTvLC9OFdKgkS79H9Jez41FMGTUnsyGmgRNUeAxagw2Z%2FN1mrCtt%2BPB53kMi72QtTl2ZK4fYkHm3IRHIscUp7%2FfnMv7dFwDmlbZHvmlrKQ2dsHNnUML2kFgeM3TlhSv0hU6%2BhjDC3E5bzdFZLJJ2RZF%2FgsxgKuTiHpufGUMskNEnM%2F3fGyN%2F1%2BA%2Fsqs8C0bhC9nOHYx%2FIOZk45MCZQ23H1mCAYoUirVM8yW9AHvX%2BE2s9yGUJUSvzAQbwuSmimn3fcg8lQYHU7Vx%2F2q%2BIZ7wlNlwyx3NWWF5%2B2weOYwiW8v4wUM%2BV%2FaUGIXRzX2BZM6Me0ULIc7%2BqDFugIdABz4dW%2B97PrtTp8ZsJsL8i3bxKDbuSrZ1e8yisB3DOrQ34D7fVLAKwQGRmQbb%2BiRN5CK%2BqYm8KeGk0%2BK9UVdE0ttghRsXR6gSe7QNEnRL4Yx%2FE3DnhQrPvxXyw1jccMZkrut7emZjs2ruNOSEaixG%2B7d59D%2FcgORyz4lhCokx6vS0uvlCe06ULsw3NJQCXvkKJ%2B28u92dzegjKWS3IYNlYGfMZ8DUJ3lJnIa8Jlch15KLzS728yYlT6YscL%2FgEgxgp0X4dyLGNnvJszQE9tV3W0DtNSeZQCFlmaqI1w7fEeGikANU%2FfUBVEEFBDfxU4%2FR7WyqPOabA04WTMMQqS%2FhURm7p8tHhHQpETq%2F0Xrs4rB949JawD0HZptp572nCOfGOW6X%2B64Ic2gT8clZCQc1YvgFi9HS2wL0dEHdKxCN20XM9nUF%2FuxihMWZvQBSP0wAaSd7MISPyKvglruH1IzPF9halDX1FMPGzzX7Z0Dz8A3wWiIQMBrnsDDBO7hqR700AqmD2Q4%2B1%2B%2Bq481s6mbi6luzWJXq3B9uvf15DDgo168n3eYeuBjN8osn5Q%2BVsNetBKMeCfmoEp%2BBLx0JCBiT8GpXE1Hee8gz9fFSgLn7%2FYQOFh5G%2FgDSDR29RETIDBV8PIox35Uz7zsArdWcy6QtWNISLO3%2Baunc%2Flg6iXBAYaSIx1tvaWg%2B5f99XvKaLicZpxC8NGczlLJkxDBOVyCEwvPlq%2Bkv88WH9GNfsYiPdE0a3z1rxaXdsGQ8UA4l2rW1hEf8zqG0v9QlEHnhy6VbBzE%2BkngkWtuUj68FJbum6XP7SpdnJfCAwLiUi0vAu6TI5msOH4a0R6nK%2BOl7TaCnAKOp3yF%2BLwf9UxMXRroA8i1ulKcv%2FQZfJaV%2FCerWZNnWvpjaRTk04aB1a5LOucvcfoG%2FlAmhhFsPSHNJdSNQrxpWdoBEMxDWOP3PSVAYddkFDA8EcGzkQZKkMUpFY8b7XPeEah5ZtqrGdGEXPSjjJFUYoRxb7SH2BoRUruFnoyJwlwPK9DQgBCuU9XjjMW6PXC73xtUj3gJJy9%2FOh%2BcRkq7qfYYRQLITopdDwvGn6jHi2y1fjy%2FmF6GhrJX%2FC7NnAD6mc5UBvy1u3qsXGvj6U%2Fnf92i0LJ3OHJM5PF6w3hvIy5r5hMjCE8pN3kqNyrFh4YJM0F%2FUEG%2BuKFxXr5HC6RG55ZfgbM0ahJhMVMX8wRvyHRv6HrgPScnd0JIeZcHmworawHT5Guo61j0Nnj5ltbx%2Fu5V3TE9kM4%2F3FRbKao4%2BRL%2FUnheZzK3xx59i2sFWLNHxasYA0OeZ40tvlvss1Y6nZhWsspO%2BE11Ra%2BlE5ybTwC0s1d%2Fy2PPY1H1bE814DvA9%2Fie%2B0vL8piL4smEDblLI0dW19g0n4N%2FG%2B2jxjdVpp%2FY3z4zGhY4agFsmxCaYnWwNx3mQVJxDgeve2ICu%2BJ341b%2FQignHdXxbMK8830elCh%2F0Zj6ek7xvImCa%2BhvZXZAKnOLdJ2QgLxiwSDYkqeATqGsF6aq8%2FQa1EaYkK4%2FXO3gc7BnphPJN%2FiMTlT1AEDR0jmlM3kORKQFQ2J0FhVe469STr%2F4FgKHu5OwesxgZ4jidPc%2F9UWm%2Fktk1jkq12WaY3%2B7r8KOVxxai4OdF%2FXVeVUhVH9NpJOR4FXWzwi4VK7CM%2BDPJ9Mz4BL0aePGfCZmki5evseMu4164eEYPIhMne6F8g%2Bd5s4HZfO%2Bk13UnJ5aX8iIcobzrHPm6V4G0eGshk%2BExLOiSgxD%2Bi9nx1s51BotALlKdUGi0GqD%2FL9CXziFUPsh0mxqi0b8jDJY9M5nNZgENqAQr81l5aLnaay9mfIRT8JHpeaS%2F%2FggOEJq2jbpQVAfBkihWCnSWLsGd4rGaq3UtzpkoQc12QH9FejyxL4TIfG6jgBeslRsJyQ08DTXuxSDg6cikKidQ%2BMMdISHPeLhLm5acPwsdpSodRbCiPqJAW7RGFzzXiXfrQDilmeH%2F6K%2FkuiCxtpCFHGDoBVlyMSxwqNAtsIz8p%2FrOfvMUz7LdbbiDWS0jhGHpKxDA05yNpsMqhCLqJ6LglQNY67N%2BL4%2Fjf7a5z4IeQuyjVT88vk9KS7PycGZVdSTtzjaxVMZoGb0hM4uEbA5CnjpBfRSjhHGDylXyCQib2NPb1b8rfX1DYR4Mwoi4OLEhv3zbxFyFCq3HFwYxm2zk34faQjCnsEA%2B%2BlV0gilKMJsX%2BH3ZxuUt7iRqpd1MkalQSn2ndwqBHCs%2BHEXCyy8jO%2BzQTpwBOvgad8PGKj%2Ba6MMGjuq%2FaT2lbCEuG3HokxTV%2FLJRH%2FETGG%2BsPGt0P8f7Pl3tnE4aN8PReEshnMUlRrkApbfkm2Gf3tC2evS5TdZxXdsfV1EGM1%2Bj4021BIvAsXx4T8HEVOCoFANouztmAfLL4gZ0Pdc5o7O39fx%2F4gva%2FppkNnR4DPjjDJZWuznMznDMKAISKl0EAI6gG%2Ful2leMHC7tn7TZvGbz7DeCNhn4k9dXuMTX8HIGFU4iyNqdYaj5Di2DizYBRisFJqUvGf2Rm2Mdpi9Ib%2Fow%2FdCL2Cyi%2F22zQmUztgk3gACWw7%2Fs6UvT58JT5te%2FP%2BL7TF9cF%2FDTIe8kbFj4LW4Pp31%2BPK8inIfxVEsRziV6RU25XCdSrZMsEqEFFcQsy9vcEyLcHLwo%2BfAHvYqeGYEioHdlQbrcrEyvtJ6gJLZFwV3VeT4ibarBymSNq%2Bg%2BN1OH2QvAKkbUUpd%2FeJdQCqqgoLvLpzrUIhwViIK2GQHWVwr8OkflhYdCZO1wteQO9IMOB1rRdkgzh9n9lem6%2Bpo0BcVJRpWCZfeYQs0scVqFuWgqGLWOb%2FvuyBXkIxrtWFzkKZIzu1vcuU7lI1XNtBDR5UggOMgmNbfkRFZFBm8VLda0MsvPl3KOH4UxxfnYkng7y4BtgVHHZIIgG254z14zI3GEgXUBQJ9OqvZIniPqUqXQdpHjWt8wNpqSUdw03V8RP6cTQU7f3N05WoZoD%2BfbMSATaWNlB7R0vuPMvbfh81HYPusuMHSExCf0K6p6%2BxqkYY3gxuH08qoKSjNLnJ1PSP5yaevSPkw1RKKq3RpVpPOzHUpeuEeR22gdV%2FuiJ%2F%2Bweb9f6WJPq%2Bu%2Be9k6sDPMpwGBWCjp9QTsPCl3YyLIYniAcUnLlL6j1Y2D9XgeX0%2B6pxGR4moiGyiwXLk%2Fen8sNBbPgHmxR3TyAL0CP54hup3x5Qh1EnYE9gk3P%2B1RYAO7rir9U5be%2BRRLTDFFSUMGO3M42s18O0WbBl8ybAxaP8X87nhkS6R%2Fw0BvIWz%2Br0u0LbEZ4bgAHCLZjNmy%2F66udnPd2EOjOEbFHwHTV2o0VHPLigkPuYR0%2BoQPTGsTbqV7deeTDLTM2lGowmJjP0cRbgZ%2FkRJC1JU6o6E8O28AmG1sVbxcwYgiJnx93Wm7hVHUnYnWb41sjNf7MFe%2FCb1H2wuF%2BHZsk%2FjLF1uTDp%2Bi%2BAdzlX%2FQQBx1PNRx2J3rAnQWEwuycyQ85dpqQOJ3bdj6Vvf3qRVXQZIVly1Y0yz4%2FRZ40zVtv8HE4a3cktx9nZ9EvWdUKHshFtoT773%2FlyldC15DlE351NskxoQkN9aJug84%2FVs7lhsvGEeE8kc%2F2BPao1wp4LR8bvIlI3BHWNCWz%2Bt4GUbaDDZCb%2BwJweh7CUPTJkbtykBuf6V%2BFNJCHsywCjOW3WEUPsF0iRlK34eH9dG%2BcyvRrCwPyxNPAGQ%2BCAdPkxM%2FzwP134vJTuB%2F%2B8cc9yp6aGDeeG%2BQY%2BxZEmkRzv8fVRa6vD%2BrJ8WZ2ZmJswvSPHyclPLaagsEXHaVNoaUlZiVSvlmIBC7UHnb2PFJTR3RdRN%2F6nbJBZov5obRvEk%2BuEDKCI0QlpVcLRPRNiTfwybnKnvoiyJVwqhRID7hbbJksS6BKCRXZnLg6QTdZ9xElQfgU6GnaZq2%2B5UAWR26kgGF45b90m%2FkLQxIpTlJMqOqdaH1xD%2BMqHIgcr0kU%2FD6F%2BWE39DyvWtpxG9swocnPQUWG6X3XgM%2BPgsTWTEazB7dvJqEA0aNBmzTgxKWAkTeA8khEKlkLEEFKetxTHpvSf8u2bHR3t2xItfArLphj1qxGn5SsNiaok29RbMvAupphpgd1c2w6SM77dDASmbzhMLt%2Fbvp13ZVwBZv%2FvKauKkfiR31oMdSuujiF%2F7dtYNGtufl5hwzgoRTxJnS9A3VwtZDzdW1%2BFJXLIqN7CIlNKFRzD873NpUEWFCbpUqQotETmD67ZsDxe7ENAzs%2BlZiXt6aanJPoApXjVash5VeEP7kVbhqg3vUzDeOHucuESDH02HeCcqOcU4bbZctRxiq9hFVBE%2F3QyumuUVIDaqrtitvIBQjrrVkZu2eMo%2BZL9pnx0A2VitoNIjXTDPyXM6laD%2B7MzNqKTtk0QB%2BRxOb0wUDwLMjQKftvrQtB3u5bZ%2FvFrm9aT%2Bai8W61o0N7XvFPuXjcXgeYjHRpYnB9ndw7NIHLJoasVD5GVEf3JKxG0EG55Q6m66paynvk90BknUOPCP30txDDvjmtFD%2FB4wvKNxYFd62CHDE%2FGeNJWX%2FWocobOuMWP0lsmiCsyma0fFJIt9sV0zMFeJ3sL6%2BwG5IcJRx1e8DWJKWqCCqFhkcVLEavnGMdKw9XjmY5bVg6Wtyr4tzuJM0an50YR3Bn3CXwvatZBO2nVgjF5WijSCsINw9TqV5UQAxeThWqiVUbMfEGPVoIo2DisyjAnrUb0MFi%2BhPkKEKOgsorIzpz5orkLc8j%2FYP5uL0FmDBkp8LMO6Z9RePSm8VSD83kZr%2FfRGGR%2ByAzMm47JFPcKmfrGjgofponCkQDmOQYyY2ThHx9yGoMpBFSSdMkh5L1wkJfrAjtst2MAbj%2B2syfPEGpEFvgN9E4ITNMwFlwc0NIx7d%2F%2Fa4KqNDVHWdvDc%2B8nY1Xax0HKBiPQtuJHH2fhEU8Sizn0FNocSrfd4%2BQlfdZlxI8oQRco5KhPZMZUWf%2FJ%2BC8iCyy7k2Xw1QhL3x9IUo4FLv9GSjsiYTlmXh3LCY71GT5rT0KFi8nSHRuwtafNLN2CBjgyJcOcfZ%2Bd9W%2FplQBMrYFuJ%2BOVhziHXTqYiEH4XKwYHXw01RiIuRfyx8AESZk9OvGmZ5GQslkS9HXbFRfdzxiUhTzL68Q5VVunX2F%2FDA73sMDEdzgHaVe6jG9gw%2Bd5SidGLTEeRt4rELJTTJMf7tMzhsd35rj355U4%2FoIuDOSriKcgRM3qwQTQuHhbNbBnp%2FpriIXVoK1M3g2yRqnRtPk4Ycx0qq4%2F4%2FNw3L3rIIvd7%2B8ddp0XKYli%2FyJwrG%2F7jGqDcK44yrI%2FYwXfhejeT80mem839B2ap6rwyli4Z2B0ujOMERkTKu%2FJKkIy2q4F0KdB82H%2FAo8b86Lrh6gCGQ9FandaKsQdF8%2BItiweIRr2tSqYELnggKThWD19XHxoRdJKXMIJTTs4Ai3AV1ycNZ7NIWl3CJKXHUuLQ7d%2FER3PHnJGYv3KhRXwnidbpKgYQIFeOwT%2F4Um2Rhw4Sz9fGHjE8oodHK7lr0JNLd%2BhcHTlHvv1s81Dd8RXC2y1GF8pB%2B%2F1uqrrAlZK2mZvle9rq7MA3JlDkxUICS8Wdw5pI2QAmje9kLBjyZlmwLDfG9O6TBLpF5SVzWduil4P5PJP8MEUTm3J%2BQYTovANb8zgO0O0ANep3U0DQ8e3eUPxKztWJktCrzJsvw8r18KwtpTK%2FZUxxl4cPtGM1kXzKiEK5OeUikPdnxMIFmcjTalTnf6XKVKMulAHjObzYmx3NnSThoJDwRne9Ce8fPrYXpFMxvclXta78EN9FFwk%2FU5lIqVupL%2FP1oA6uCqw9wuIzakOdBjCJL5tgYmlXqJGrNDIBgunHyB9nLYMj9OxpFxQWSRjOGmC4R2x535OOjy8EFV%2FjgPk8don8blJbWqmpxOGvEN4ymD17RALFPjde6v4zuHAjdRMwREFI7O6hyRq1VykhREuesy1B9HTwOaLPdOGWoWcwPG30ll6dvJKrsvjl3bDlEIwKm68VLJEsBMesCh65C96B4gEvt6FZkd9t2gGH0L6ynubSiMzvcUBPSyjZR319Z02bgejr8s%2F%2BscGopa3%2FvrFUgz87P%2FG6iMCX3N8uJIDLZEuip2EFpcTHOOAX5%2FCOLAJ%2FtfcwXhVGA3ZhHNrkjB%2BObNRZMCmnbilGPdijXk0%2FFr4aCHjGkR3MMNflTzGotg7aMLIY2yUzm1BdooavNlC7rc1M%2FxpC0cxnPq5C8IG0%2Fk5r2Pk2Ia3UDFH7lTNQzICvJO51QMS0h%2BmjRnqasjNdWIlI2zOcm%2B1RJzg3HDKe5QUYYXtMhdSE08H%2FL0TtN%2FGmvKz2UOp%2FGuhl6DcUdFnCVeDAvtMGMeOMvaKidtvoUOInx7j5wYIk0jKv2aiGUQE3ARP16iZxqE3VMr%2FzGVo1QVboppptKFGBNmrG8zuuFMA7ztFU%2FXybrZMgmDlDf5qMMm0loAU1J26Fg8xZjNMpv09s%2FJRy1WJLL3E9S%2FgkuHw8kjeupUkhF5EOBvUbpIKrzGPOfG95NAc254%2BV38iR2V0JvCL8kXtYxB%2BCH5CBIWZP6NPz1XymdPJWd%2FkOt8LXGTLjPkEvojhMW%2B1lRhtXSMGKlVH3IhtPPUzRn9eh0i04yZSiD3dvxqsWXC9ULxhvr38pLNltbypZ3sFnD69axcqlCc1DQEIfcJuoEc4RwTzVt1bqATi75iVX1%2F8Xs5WXzzClJCG%2F5ogxDYEousYQcC7rHtGiEQ7pZAOi%2B%2BX%2FUdBDrrBlbZqWPsunNkzBv3O86%2F4nozWoJKpEHdt7HOz8ZnddVvfvUWs6CRKHvJWEpwGfj4aOHfr1U1QcSMToijpQFMQSPP2UnyaOgLKGETImWNTHAGzoO6d0AYV52ss67F4Z6vXB2eeOhxCc1jYv%2F3JkJUvGTyuP0PbP9e8HqQMwS4sIgnvp7WnB5DmHg8u%2FUJtMtsxuvFrcv5EBdIlwXduk55fUOSZ0%2FlKKl1nQbVSdEAl9kHmxjy%2BzzeUYCC9EhDm1iKJoYDTNK8uwT%2FTdN4WOVlK3UMAIEuD5UwWcSQTapq%2BKyRH1P51KLBlOerV1E2nQj76Pi4ogfgp61PsUbrN%2FSiQRagOSLdXIQArv97lzO68kotLsK%2Bmcefzai3UZy%2F2LNdsbzNxmaAVDurVLgNFtCMpG279KgT93uWHiWghidqnFQMJYWbI3JI3WD1RHPfLovYV26gWwas5dMK6MaP0JIbtn6ei%2FR20Z5WMf8AjcwDoI9eXJaZPwadAmPkqMJ0RaXd%2BjJP%2BXn0h27Zi7o5BDHAFXNEgqqFwx%2BQnhCU7nFq7s%2BCiYqAXLVkeF9GCV%2B6YlFsTFoHUwmgTT4ZT5onKD6ulffKX9IK8vgBQ11zXVSdnShh8mxdxLtV4Led5y7gsJiQAGef0g5du9ovR7LzvJi%2FkG%2BqM925FTV0%2FjlrkGY8XimcbQI28d%2BzBGBRd7whVNH28TeMmhHeXiUd9nFNwHlVoU3BpQjZKiAxpTEyR7hmNXrQXW2vcqM3BYkzKiYfHZGBKwa2JXUB2SvRHTf3BOHnyFY4Kcph1NAJ%2BKV4WFNKVH2jv5Vxiljv2fGXNjsC8btDNuoEGNAy%2FCTz1moqcIZlA6AlstfO6Y%2F11K2SbSSNnTy5Mj5gjLkYDrdau87ruPoMcI05TJstzmNMvP0c8pypUA3ulp%2FVVzzFeo0RVkSpA1fZZ5NyhFFVvnAP1e5TqKcZW0qKqWhFSo6lymfvywvr9fRDwGSdpspoyd5U3FmOf08dJ1x5wDsXYNynRenlRo4x3%2FvZL0i3VvcmHJ1yrVVzCui0e5taRw%2FwbiUpop4Vpy%2BLYm6EWlRHgi8b0eLQacRIUlFCldCiClk4n9f83y8buhGPeJY4QEakl0XxP1UW8fm3EnvAEvIDDpxGvyYPzdDaBbvJ9ZAYdUIJ%2FwibaNvYgV77YTP3KfAEd1lqJxO5grMoFY4cLo4%2BUtLm25sH6ZvNTAYPM5yr%2Bu%2B%2BaWL2jzxB0SUBo8dbAv8zMJu8ozP011XwNzdwi1GPoVN9rSaZboza32uOGNFu%2FKj7%2FgEZEa%2BGPjkWDsmiOH2j2RxpE4KYLAlXC%2BbB9WY1ryAQ2mDIeMeZ4x%2BMtt4GdbhlZeVDvG83UprLoqcxM6jjJ%2BDgfX2RF%2BGk7uy5hyW%2FW3DnuqCqMYK1xA16QrmmzYBGiYmIXJ7MGifsDmWituf7M54cdm5tONPIaIPaO5%2BVYtN5%2Fkf1QUZgYtsFEawCFXXh70cqe8YDx2B4v1Epw4bLA7OVOOQnp2W3VmbX1Aj96ufLAv6ngxeXjgntSUobZ6t7FIbTs5cjrjHUSVglD3C%2BI%2FwABtgxN%2F3Yj%2FsXuq9FEIIPNZvI7hXgijJoy6x3kfe%2BRXMDAh0QLNOE%2BJlA%2FCsKvOCDlj2g9D0XqJxCBxLvP7GhJaa99fZ3Zcy4ZDDWnmIOt%2Fi4J5zlAzNAYoBWvYESoW919f33VukZtyHicefpVvphbjygQLWHJFCQO8%2F9XqjoawxpYcnWDEwImxy78EHRqVoZKlMYZWHReKZNnUYjIgAH9ajwFDeWLT%2FP%2BPqOxysCme50XC9YCMB85XP3VykrGCcYZ5%2FEiMcmL3UAbtfiDteqCBNQkB%2ByMAa6HbmPyJhF1rnV%2BnnesH%2B2n2q6Apg6LVP0OoeOjK4HN5p7jGM8oMjnhB2uBOas1E7%2BAHiENjP0ZfWOhk%2Fbaf1YTzYPMlfwQXEt2pZUscX6jYXeaFZzxXY1A5RyeEXwfIudFYJcmxey57dVG%2FkdajSjvjFs4kYUo9iVJzU2ZoG%2BzN8vtUMqppPKVOQQxeUnHJZ%2FQUE4nTDCxAN9ZebU1xHOmS1XX3JOnx1lwvqmvDFbglnag9baRnhLEamMlL7AovzuYhaw0MFua8CtbJeiZzLAV1qAwjQ5bIJ7uj%2BoXB3qGxGPaHmhm%2Ff2Oj0Jox8AcYLzw77GomGQRaIr%2BQTWz9VI0KsO%2B1RanrDRG58wvodSgzw8IwCJ94yf99xA0IeoOi81g%2FcMweDGvLmQ%2FSAz4OQqOZ2e5OWRXfWk7HdXXb9uWUhwwK1wIiBM9ywaU9pHdM9JOMLgAEQyJyAcyu3PLzeBYIAqmiEjr7D3c3BDMYMOfCZ3DHjmRwObKsb0BNkOYjUEODzoqCsUsi%2B8WjGu6qzRdwOSLDuPWT%2B%2FuNh%2BYBaDoBObRgXxRvtL3rtEtN6GtmMTrJnAf2vfYifTtUCCSZwtAcaZcAZ96oVcSrRNMWnkQ8mjsG%2BnmByCMD27PDiUJ6NdqUJ1t2w%2Fa6yhiPs0%2Fj9dDR8LEZI7H6RAMD%2FmxB2Iv3bJbQvIhW%2B9JX06BHr%2FGeV1DhDgHQMMHAVggG2QZ1ar0PusWGgOPe7j27LBUEiBAmGBTpeisIXlCHgM4GgdRr0CGxipZSaW4zV2KofMok9GVSLAg9yDJeN4zkZ0gwfLHwqBdx%2Fcd2UOSs%2FyPGhQl2pierlDP0%2BT24fvcVcXQYotzqdd7zMePX24HXynCNxTw3sGqYyp15it%2Fhpc4FWoEnfdBz8JsZ3qJCkqiYuCVkvFS0%2FmduOxxGWixjhv%2Fi7w99XSsxEr0C8ESbQojb9%2B3nUC9OLR%2BGSSiKfbH5ftWJ3rZNEmNwS%2FJNEP9vkWI3lOgUWs9MQxbOo%2BYa4esBk%2F1zue37uzc9pyZPfJyMvN5hqrF9AtChWFUWKSfXGP3GugsbZ5m7x8m27Dek8TuoYLoail5o4kxoOYpfTsvobvONh21Yu6m7DtJBuDqmspeSoVQ2xwQwVTCKVkUz60VIcgth3c%2BtnghhP1xH0qrY4R3%2BaB4JltZc%2Fgdpa64NfFcpl%2Ftmrzj2cftNzpJnU5kjUaADQwexE3fzzYd2ZmJ25WEpEi%2BJ%2BS%2FQKHBoLBwF%2BH7LHZTOZ6mje%2Bs5Tof2Z%2FmlQt7WIM3g8cG3m%2BPpSWbwDMpeYbSsTv8EGOZVBblDw5nlQ4MyQOMQf5kJXIcWntq3fcqZWZyQ%2Fin2Ooy7TzSwyg5m6XbbkOY0ODOdwUMvsD%2BmEzILtgZGGpuCxwnFY%2Fa4GCHRr1o%2BcpceOJCHFYrpmcUGngyEhs7oZlzOypnOJ9Swxckj7ZTF4qOwcCkCc6sGZwSOOl%2F13OPuf1DS0WHknNjUfjuqC4vkxVbmd0zsWIGZZCFGm%2B9ONUPyUN19ZpFJ8cv1dAz75h0eQZpIc0siv4q57ZaHYrUO9Qd8FatDbnwYB%2Fy2F3pl5L39E3FiLQs6rUR2kmDbrz41ENoSZY7CGWz5LfHhnpt6ZjR0L9o2uCgc1GWkmA3vjtB3dVsKXJmTgbCpnuLhm7GA6FD15yB1XAmaNvxt%2BnXf8IORb9TcFp%2Fl%2BfRD4tGJ31nJWREcbUYXGQohPVQCAXzVUF9QAr2QrWf5QmWDu%2F7%2FkDkBVaqEUSpVEztWlRgRwnTqroDYici9hlSNhCN6tfgLL73QJufeyVVXvpCZ8%2BZRu77KnSQ39MypmqRZtBoNBheCkH%2BRgqGqwQwRnEg0WleF%2Bee9GHZIYKEeQLBeyIoGHSp8oKuYiBU3FfRVfhO9YUbTpIpqnlEaPh5aimO96RrAXf4SRSCyzMoY1ZAo%2BiSkwi%2BqwaLSKZn5T5j2d7NOIcCjQmPRHU922C%2B1kIWuCSqjK1%2F0Poi7biQg35wNoMiQxGdJPr5hewRQ7tQ0miG3NTlkUxGB6VKCQjZxe7z4gGr2NqAQn4RURq%2B6lfR727meRUqlPqTh6RePUKI8WgTV76Rheg%2BdUzuMJfQO4xXrRWb%2FLStKxUIRp2sF%2BGySydi9iFakYUhshCjVxuKxXJ0PgyFMe4e92rn7tkvzqs42dEC7H7habifAptKM%2BPCQ89%2B7eqSWP%2Fjxga67EQWTBGIKGAWAfMpIw5xgQs%2BvOmRb59CfKLTeLCMz1eyDeNH0pML0HB6i7OIAxIuGAl4arWdduL%2B5CHR7%2BqcGnQCzkM%2Bc0K1vt5lCrAEdlRyGTXQcMj%2F%2F3jqBsvplteoLj1yEtxJ%2FpwM90gOUowTb8l0LEXOJuZ4Md71JYQ8J4uQgs9mZ7CINb42w4WrIGypAa5XHiv7cCPLD319eclwk1mBWTYudWpwP17sd%2BCsdUutZTmbr30waLc75PE66ZGFf%2F%2BH57YBgW5VqMGjHE6qDXB4xKJ6B8A4KI9E2YiHSDXQcNuxV0MbT%2B3dptONW8i4B0FLER15L7WKHf2WFIIs8CtdoNRUL2xNLRiWWdZ%2F3lEyN4%2FGbUuTCNDhNG5WipQrPgThbMkW13ZuplPgP8CQNp8yebwdJWzpFmUD06NOUuZQ8aWx%2BCNGnE8L2CGE7VfMHlUteIMl85Ys4M1pHLPQ%2BE4tr78PVYokPnGby010Y6f%2FFCbTow%2FoRHrbYdGqkABLBEd8q%2F3frpOUoo7nwx8UzcpLQY79oOxwJtJedEXY%2FZT04E0c%2FUiW2j%2F0p3zsyTjQZ3Oi%2BtSONrVH8X7GOrZLkyHYaiHWQsxgwLxUbzkNcDWZsE8fOtoWyNVqwpvQZ0nuGSrYOrbAq22Sy40UGLAUZkMscHsAnIgjHLVwL7ykyDYPYvDVZ5aMvlTvh8I4y%2Be4zfifiqxBQ6nzITwN%2F5aS%2BAfkty1JyaIDCCWGmQwWnzwSR88VsZXcDsOY4thWtGcbV3uNAQpJWGmhBoVoXjEa5xP6sAh4g4h%2BEUDG1c4M2gHC90OFnkqfA9QZ%2BVOq8ZF5qxFXQJ7c%2F6C9O6ndHgxc%2B%2FFlsZNqkd5XRWBTjB1GHVjii4aPsyBrLI95dkmSxsswRUhGGzvE5jq%2BZaYJVrz9BhRLPOL4j6d5LFNXlzGhxxvYU8FsVD1fzEFR3BjHi7oezjAeWR6rwYmP2I1VhylmiaBQPbQNaWIV8wYFZJNHmx3BXjYak4sAcajCAF7Omn0Y%2FFMsZR1tnAGY%2FPOIGezXcOpFIItACRz%2FfdCZ0ZSp%2FzejnlZyYZQXBQBagGfEjcGjTi7529uiwQbcDmMNS5heZQ%2BiCy3%2FjZ56IEcC%2B25GoVhnFIMWsbS1OKZDx%2FaOH3P4z30CpozI73pdYdeEM62Dl83HySvvJercHu6r%2BbXDZf3L4I0nX1oXwY1HnQjKDaT0NV%2Beb5odRD4ZE%2FILZnurSABhFeEC1u0HTEpNUxTHNTc%2FES9ciWwNZ2xfkLra%2FhArZX5NiBzw%2Fn1p9XbntlY%2F%2F5SNkrNF%2BNcNkAgwq8HLqYSyhe4K3dmoEjNT9R1PfZKiFowkAIr6Xiuay4H3iXnFovqg9N60Qbgq%2FfgbM1CJZGhGTIs8vzIeuZQNcwB04HMnXcCC7mHSnqWifCgFJzq0fKViPr3cR0flLlttXnnKhDlh0vwmPUkUsdAf1cMfqk56RMZzdrNiOOoB7UaP9GF44NOyfz94NBi2i63jcVnCOxOZxpRdHdjJuinCcxeY7MoYwHskzjPtzAClXyx5m34JzV54GI%2FaImb68GyKlgL%2FEqNW7xtV1J%2BKLHlftvna87Lx6IpnQB70j0EbPf504dOZ25F3B1hevqSmZqkc47qtjHWKWv0OFXsW%2B06e17mhiY%2FDoTSGyz949VIhlHxFcoR5bNkGeHhAShSVDmjIpB6zT2bJVWtPd3775iprbUotJ%2B5yvJsxZrQIni%2Bew21AubIQoQuoen1J2cR2Jypis455Sc28du7rIs4PvvS2bXnKR4OdZk1gHGB47Vy3Zwa5DthyRNvcMq2dtM%2B1bM2TBvagNXBdMj8aFMAUt%2FsmSRi7OvcmAZvbKacS5kkboqnrVcIywzBeXUJODGgqn%2BkYg7h9u6juyOBGbyUoLwM4vHNQSEJgpt3I3FFnaua2304z7nrwsZdvcjQkLdhBPkFl08XfAZtblp%2Bs0JEmJc6Xvs8wLy7IGC3PpIfA1uB7A5dKu%2BcxLHj7VIjYlS%2FNTSyloQn7UmjDF%2Fwc4jOZe6kFHUEjUHfq3wsXlzICqUm3gPclWC3RD2uMh9MQMYCQD5qLfZTektSB%2FRVhlkowY3biyOqsgXbraN6Tekh9BVcBZT16a1WvIYxppSdd9b1fV5mX5atxzJRcsGBTbCeWnNgH339waF9yTwHeyGuJmoQv6Fn4bZNZx562oEnNZEcR1vNKJHQzE7Ux0t87F0gplqbU7Q4DrGp%2F%2FVMe30Jxr9Uf5mUn3kfQ%2BxIDLMuoOxa%2Frd64ZPINkVW7JNTWPDaoDwTeBEqF2OC2SN2O8h%2FFQBxLcYZhX2IOFCECHFNglzaHaq9SHASUL78c8DFW166SHr%2Bt6dA05G2yHCWTYOGwOb0Ond7mknGF4qSwz2oZ86enA44wdDh9SfBWEWPD1DGYYa4Hyfga07L6dn60RAfe3TBmtR32SVeEifXpqgONnPLRtAlrx6D5ApQlXTr9bnzfHvZGtMQCWFrMThWCyr0J6PByW0aorGb4fYJ0urSlQw8K2SxwWqHhVRFsadN1JQ%2BJX3tbWTtcbgvWERe%2F3Fa09M5bplze17zrxf5E01sxzE%2BAOV6avr%2BDdXE%2BGoZBP5zQqTzla9l3%2Fa4wjwAr0xNP%2F8eMkXvPTSrxxiQuVJa4S6me8bOtkZc6Mu9q3pwsQQaFjeUB%2FH1%2F9KzIs%2FHxe1A5ZTOt4pR73MNE8GP2XmEmd8beQjmgCifReD2chfht5tJxcp1ypjTOoB5ziDTHtKR163sAbbepIkiS%2F46XxaZ7fQOkpe4g991w%2FqgcnHvITPfplApK09FZcwCH5EPREyE4QJExoNxF%2FUMJAFTa2nliPAurpTyh8xRasDkUu4uZvH89EI1xriyERjYOA%2FSBhfXvYNcFjq61uu1FJm2AhgJFwyYEPvlCQURke81%2BCYTCk4YdGvL%2BtVlJnz%2Feo1Pe6vfgxUbHIOiN2Zyl9%2FUNcC1W6oTYxtWBh%2BhuFSjK9LThlhUDFmqO49GcWC4K0AK%2B4A3p8VP2KLX%2Fzw%2BTwMZkibWzUvGkOkjyjDmpQGD0JxZhbh08UdnFkypvRcMNJetn3aCttIxxRKQndz8tckn%2BNvwBqJm0vN0anR4UsndWqKp72REm5kHpA9zDAVZ%2FkvBuoAtSlYipWw9vo1BFQ3CbuzEsmJrXGHApLUhYrcwAkuOUpxKTZrUVJmPjAO8afxruQP6y2xqrbCyBo0rGf4p13BFbDIGDf1IoVq4Z%2Bfg1sPTsdPye40PYnlDRlcEqMW1ErmdVbl2JGgj82FhZ4htjdlqWVWL2OMdRk9qNEip1QQNCqMm2X5w0q0bV%2BPITa1NMgC6%2FocYdid2%2BiM9VBQ0JTjVvIV8CN1xjIi3pm8F1WjF2%2Bp7763s27xoxGhTmTwYe0LAmyM6Z6qICV%2Fps1CuPgAZh2OfdPJDTWqpqoFZlMmYcTOWDCEQKprVXG5GsXUybUg7tjSsCXg5vnS915PFIxbBCEJmT%2FOSAPH1I4i9Qyy6P0JLiBNflSlC9G0mSLLISFKxCP3W9gw5zkZcR%2FmkCeon3QUNcMcNx6Uvrx2lejYCGfRVUgJ0QXZfinSaP2g%2Borm6uB9UxUvpweJ10anghanh6UcjgFElud0lMYDwzCF%2FRGsxOb9LhOdbroh2rbRYViBZGpMySaVkbrSF%2BGTJ571wwih3thVk6ve2xR9AOMZyXk3we%2BORxCxPzXKlycIQw0xr2oyzHN2G914JR8w%2BgqRB4%2BHUvQ5B6c7eVf3UZ0jXOG2rLB1xWJTNN1cK%2FcBMYtkAsQKgLkemnQkJpvoz8t4Zbrr3HI%2Bb136TcLmZbZlDD0spi7RXfpPDRmw%2BTFA4GWm%2Fm14u%2BXX4CQNF5qvr%2Flmi%2F4fRzJwNEn%2F3Wu4i9MZ6C8AI2VRzeURze7JUWjhC7XZWjOCQNfbeM4fBezKe4x%2BiJFiiLHh6AudIiiQqJXW5Y0OcXjVX9gRydlvlTj%2BiPDqvtutyDFAvaw1hrsM2VDBYRYtZobLtiepMcOihKLti6PZ082aFbmXaHpXqgy%2BNSv0xcnX1ESdqkn4LJpdPOB4T9A65fLJzXaJ7SPkHRttpZu6X0ti1ChYJhG%2FnGrVUsiyUGsmHx8wqXq0c2EBPsxcIHO8rRpQZuobeE3l2aVZdSB1roRV%2BCSWb93NQuNEnopoAad3FZVrPHtMH2eJ4a7Rvsvg7A4ERTaTWCYkUXKVYl5LB9BE%2FlgtJeJKZBszd9B8gXegrT0GNApB70vr2B9jtztsgDPWJ2RdBEKx%2B7iJ02JbVrFXdfP%2FQKAbN7YohQJlmKzuX4CHdaxOgJGXp4s826396KZShMDyHSIlQASEjZ3FlwZn%2BNH3rqErSonraLgMsb%2B7vx2phKjRuUnH4gN68Eg7SnjjE966Mlxw8MGUM4p5m1JXMZNVD6ff6xbLPq22EpwyJvmjExs9zvGbJvQeqZAIoHwZzyKqCGB1wFzFCYgPc5MIRUYUAonrya9h3DnRecXh1KIpYrWb7xCLIYPzpBlzBvAI6vk5RhjH4Q3nwdzyfKtJlcUtF3Ko08OU2OzsCN8%2F2Jryq278KrmrLAtvcHFcLMJy898NjT3bmGs%2BuOTN%2B%2F5Gk3wn95y6AGguzr7w7rlP%2FVR4CPJ5wzh0hD3ptF8AFeTr9uqpkx16a3VBhP26S9KzX5OGx0z8yMQr8y8wUf25Z%2FuFhzMUWKf470mI20M%2Fc8v%2Fa7op2tuHRNfwJgRJcJiZ%2FF8cikTNSJu2sdOpkphhP2%2F6tg9uFbH%2BSFUKUJbaAKAdZlMxfFkK%2BYtcU5knT4UnFEwxL0Ikv6JSZ4ximF4SdRussKKZp2d1x%2BQ%2BBY3nH3ouIWgNu2wxt9c%2BJDMo5%2Br%2Fj3VB5YBG1P23w2eEIPf1IDjs9t8DMnznOVzh4SeKTklaN5E7VKs720KGSL1jGjYzRAexPC6ZDigZS4dSIABY%2BVXTW6Au3ECafWr9vx4iF2FXU%2FAWMUS8jBSEsrYABjIsXB3T7CvLu5DbTeTL7PX2xG0eMhiCQNPTOn3V0jIIXRC9J9Smc9FilW6cnXSZRA0ZP4rY29dM%2FvAgrbejFmTmmdvTS8qgIe%2FTFxk874y6m5jyl%2B%2ByumOa5MRNsIlrWEk%2Fx6HpU4emFL2Pm9RNWF3OzCk0ZSBBaax2q1%2B%2BxlgzRr5DUjpu7%2BT%2F9akl05DDwNMlfiHs45j%2Fugr62n4qTD1YgoTEGt%2FLQFykv%2BAxt9qHKJkNUZ7O68%2FJeaTU6vziQur22PjsQYutv8whRonrVIHyYi4P67hZuKjpsz2MbqePDCXR%2FU%2BD%2BVBuneWwSHQjXSYCVZY91k5wgM0rct0wKMEQCOrjPDdLLbeodzb1SamHzEOFDf2JX6PsvwWKlQgxINDpUP4iKjVWjXEi7wJVR6zl70etE%2BwFTHAMG8V4%2FwMnvTUrumJBMqnJtmjajiN%2FDTuOJc25bgII2p5egUyrjKx%2Fjq5Bl2jEVtNQRq5FdRnY%2BgqLDYMz7DHqui6x3ZkaO8nfFzm8pXxsSwRvyEFKXMLSu%2B5%2FoYSoxcADtfz4rAlvRbtFMn7soSSYchkVwXzFaVT8k1b1iTbmT6Yn2C%2F3pcWoD2%2FpaNBlJ%2FyeX%2BDSWwW5HoYs3l70V0sEhNMMK04Tn1JSu5Q31mEcEH7KafOBaDEkHI9Go6oszSHdieswU2JC5TvR%2BKHTDBGNTNwcLkAUrHNxJLEqy%2B9JvmUCgElxWXXkHkIXup%2FPOvI0tVyCsslV2LGgKXg9F0eaC7gwx4NQrX59zkELcHj3g1bz4PhORYXlAfrKoQYpihf9%2BaV84xKe4F6l4xKIs3CAuO%2BmQoavLvy%2BEBIiuRNcfCZCICbs%2FiD59HkfmGdsEcreuyxj9Opf1Cp20rBWZCZn3WJqXm2UUgs2NM%2BHVY6Rp9R1kBXjGDJK1R8rGO0ACA6yYZUC7jOAX05IBbt0D3J%2FqfQiWXXIe9eYVsnAV6rrogbRq27g%2F84B7LpC43RIMitSJrXRk87Tbs64vUQksfcPSkHER3e%2BxJwM5FfhnX4Brf75U6fxlxtYU4cyJ4J79PfN7g3GM%2FjDFYLVvFQeLvx0kW9i5PBHVnTv%2FV4ptvz8Vz0CM7Q7fMGIAz4huyVbP9G72sCSloHccoOl4bBKdJvU0Fl3DyVqc8fJIaC2B3mjoOIpcS5DWDjnVpLGDherewWGsUEMgcObPIthePPflt6xhzv7PylcPfvKj7PyZzpmiEp3zEz9lPJr%2FN3ibSoFcR9KoRpEWfyOUg7lnaw1%2F7KdbODqO5iDTBDoJgNKAZ2ztUH7FDSHbi2sa5bUVy2vqousjkz0XT71kL9bmmcTN4GPx%2Bm%2Ft8kSrGt56wQinqlgg2brBvqzRbOW%2FeQqYpIdcYoXoeS%2BJgPJRA6dKcpgSJAuaf%2FNuVr%2BCQfMGL%2Fy1qa7FePdnht3VEAN1vtSKOMCAAi40Tgqy3uyMt8p6wfANzOKXtP6RG4%2BH39rDwvdgG%2BfzVCTnke8xHPOtQfhqmLJfexvyykmmPRMD3Z01ysZqVvgOtcdnuEkTVs7da5b3GvfMH4qL41n%2BuBgACwHeERwvZexXZxAzzZfOUK2iO0upkkU2Hay2b%2F7JQsQsl5I9k%2F2xfTktu1%2BAuCtQEF%2BopAZDDl9MP8K7wJB6FqGtHi5WURZCh9m9pTW78%2BKBaFMsL7FPNGiqOL35cdSBsojkhgtgvtKVyy27xSnCRKEaHQ%2BfsHh69W8wcGP%2BmouJvw9xyO4IzqZ8r7r3KzW70KZqraFzXG0sMuzgnIGIjSIPv1PBE%2FHvF%2FLKY68SUjLsJE8hrBhTusP43yjTCbx4hCgv6Lof0%2BftCaogBmrzfv8DcYAld4yvBsSMp%2BYz7vXz8pLH%2BzJPF8RergjmZG6jO4%2BmQkccWwMOsdMxXgHQRKShKYSA4PyefnrbfpwJUyO8A8qswGl%2FjKjLHgE8kluuR4BnkiimeL%2B406kkdu2imw4Mutg9yV9ZeKPVdNeqy4x0si9MXVwPXhRBlYUQET94SA54%2FWt%2Fko7EJDyt9iZAqckQqs08geC5Aq4ZYfq%2B4BzpQDVoB5yxqA9RM%2FwJIiDhbo9ceknqBpNFBXai2z%2Fjjuiwzpci%2F36T8urugj97yh%2FxpIiqHC4BeOmZC9YqKzE7PAwh60cYk42aRx9P10DBJUUSxBuj8IM9%2FAQHayllVy7kbXYVVHnFlprCR6DByT2q3diD%2Ba0nUuFk%2FRp0zW6gPJPCoM%2Bl1Fmx%2BVkHPdxYZ%2Fo8Wnwxaf07%2FmecjQ1M6yQ%2FZgv%2FuH%2B%2B%2FMVHu8tDNLD%2B2dToRmegCoPPtW4s38q7RR3VdutqGysVLSzKmWCc7xK5QEZkTie4Il6emrF%2BoNHPUf%2B90rArXrRe2KtQr5lVrOQTTiO8pvAHI9lq9wxoGD2ajnlp9YsJPPNva5oHgPp8dIfSiJakmUj5ieE4Sr0J9x8%2Be7NP%2B2UFJIAY7QC3J5oaDjY5NSDUxwWo5%2Fzl4cZO64KHsuRhxIfIEByFlNcCy3ghkaLoS%2FsjOMmvhEXZPUyTmwcELO8wctP%2Bk7U6WDg3Cy6spvkCxSDe%2BruH2bzGeSsIDwNf9V8T70PVlSimIn18sxy0g4k6g3B472AN2N6xWu2SUnflbaLNgRW3YndGlROj8WrvIrFBNk0RioF2VPFFWwOcayYTpLn1hOGEuwjKg63JOymha2rVACJCJ8jxcki7lwAYfjbdALpUkKg0LoQec4f4qWD2d8cOZZ54Y%2Fh7gbH%2FkycqUMcUfW0HlKl79naa5NDWL2a7xvQiF5Fqo5jR4wQDyE5oDoKoVgTsI4ymSTmPmLH%2BcpuOlZ3%2FaV%2F49IaD9NL90KuGwD%2F%2BHMdaali51JVsjgr6j5gbdIrAGFZlVT4gL518LZdJPYpLtIVWsvUf4SEKq6DNPRlEDDtgz7VbEo7rQgNxpx62j%2BVQDCkn%2FOw9NxcLowkF%2FpT7u4kCLq4nyL3g6%2BjO7ig%2FgiFFyMTNNTH6MS9PxppeKAY4eXDsiheiRnm4XkfMW40JfnphmmXYMw3Ih3nvAwNCMNIGe%2FfTfOe381vFHJthJ6kkeH0Zm2KBxajiVdlJ6fQN7NcnWKBAE%2Fa8R%2FebzR7YzHvGk07NbGKmH2d13xAiv5gjPng65KE6LHK0ArEW1D6cNA42duzQqFwrQKvLiXtnDxPquNF%2BPr%2B8QyWXR9sgUA2jtl4BsBN8G11tGt5v8yqAYB1C1WlFCgJ3qvcFV1uSaS9XnMmSDBq7VxSrZyHMZgdBL6hiuGqCTDx4EVBATBVRV7PiLESw87%2FFo0BLE%2F78xco7HCuSzX8DimeOGeclfpeO080qbXwsUZsppoRJGv6jUyVDk9bPT6uIGnKzTf%2F68FoXVMbCGp2GXhaQn7boB%2BrG69WEcLl53OBpTcNiEK5zc6kYOStm4hr4YlbYQccExUOUQFmKHbKB%2F4scaJXy1WC2trOyDxL%2FVW4aEVE5nAyv1ogkFp%2FrFn5uOsFBIw5TbvaKMmjcXlIegqZ0pvjfHTZ%2BeZ2fgDfGXUA8rUGw%2FpUrG1lhwXd4XfSH0vPI4imp4uaoTitrJ7cPvRi7Bbf4WLCP2j7iu1Pn2eMYcI8iFZlfBkHaI9x3%2BRWcN3S5CAZKVSl%2Bn7MqTNiYmSBT47KzMTZwdpnFum1HyV0uTcsrviMUdR0KwSg76bjbdx3od2k6YrbPMnICbpVMSgXgDp3o8Ma6nEANnqpk5qFSNwOEO0lONDBRZajQmxFZKvRbkMt9jFEUFFiUU21S7A5EouRDyTFLT7QDeWsvOCpjYXMVmHiH0oLIRE5bZ4rjApackZC7OfGfSH2e%2Fv6c%2FK1RXvhTdg0%2BODsLnuV6sshM%2F8ILtRmiADQswEuxu1rAfzh0019Te00bixFpZpPOkQWRatP30oB9sxc38SShOky%2FO4AlF1B%2B%2FnVPVQoNmWMIw1YLLLI9RtOhsqzpra09alQ5gkFaCrR240Lo3GuSk%2Bre0qMGzSrUNmwTfKoIoQCjnZkmxp54Ipe%2BtcaQpQGhjoe6G9rG3xqdq0t44YdQ9qBafE6eBO6OQKEV%2Ba3O80cv28vsD6OqNDaWrfxDlVLKO9F1dpeZ7ucUPC8Eb8AgXfdvLh75IVCBt0hhLySWmeicghApdPe9UZXnMhycRtkwk%2BKXbZnDaGTG09K8PZKYUJj4KcmpgBua0ro42QJkQqb5pU6KD%2Ft9KdHuh8W0UA05QqjHGH3uHzVhqd1z%2B8%2B4QQzE6IEbEyZhUzJWeHt3s%2BtapMvCnZpdf2rF7OKQXH44vYAIcfNwQC3YiE%2FnEKVWv1eiVEB9DU10ALHf1WIW4vZ5ZuU7exshpYZrW562AMDdYKKtCIidRbN%2BIfHxZ5a9ieTXl89W7ohukMixwHajt%2B0dNGQheIB922sw7F8f4CSboxZGW44iteVMd9ec7GUly89OKhNd%2F091VNSPtyRJDejcdc9Jp6P%2F9gAsMWMzlnFVx3KqQw5uDuu%2FwXPLFS8hRr4VqKOew%2BNSr7719%2FNO%2BLWmFKOnWc843%2FD%2FqVpSsBHYJBn1KdkBbDAKgeoT%2BfkN174Jd%2BCaqwzKVEhm0LeLGG60IwUmxA3rDhwRv%2FPB4Qjn58f74lfepOvKTkNWvYbOp9c%2FfsMqtG3Y8MIKlOkTYoddArMa00umbTeOMTFemZoaGF%2Bzh%2BGh3aSVLBoCt2480I9XVzh%2FJHyI7erOhelot0KlUP5T5i1AbkAPiAcnf5roZ8WoDOzRd0jN5INTYA58cfycYhul%2BrbGX2AFviqyXVMYjuN53j44vMwafVl%2FH1VviFm994E3pB3lLeCou5Vv0xk96zu70fNf0mMRnQ2BGEfj2ev9IAVRPv9rFXWIK%2BPWjO%2BTcglbcacGYvxaO6sg4AQ4GrypW%2BBjLw9bGDDJxsbqmK8bg6qNOf%2BBJA2MrPLoUdrbxGFmIzIE9rmU5UjrXf%2BfQjQF1pN8qrHLLDs7TL9GetqQbGiVBYdLO3dybv7y8vQap00HVsx6w52y9QzR3S0rB59v92t869ljIkWXGd8jJLHSrilMm6NEkuerbx5fVyiGgIyCC6UHl2MhtV9WuXh700ucqZyk%2Br7y5Yb5p0pStfzwymRqaDNoM2luvBWQBec0DQ4eX6yuO799I8SATsWd8h9YPjMcDZB7rMlFAm2m99s2HFLXpQGfmHyiglBAWw2X0%2Bf%2BxNWokomRaK6ltgTnLGPjuxh7Ihes2fgXcEcvNcCfl%2FnpZcAfIaAKipeuinNCLnSi7nTU2uuQopwj3XnhT8Ag0lIXzaoF2NmW5GpIgyPt%2Bhd9L1axlhy%2BYMk9CrAwMVyvRy83miutVcK2IVfJ%2FkpH3iaC%2FZ6FQN5l3XcE5lmqat4qzS1ANq0c9BpbLeIDaYwghi9g%2BnEhBuytMdzn3umECGeDGuB%2FlBeWyNAbaG5ouXCNpsoAN0dRRU%2BOYoN0vizavKmwd5SA9WQPSVK7YEpaWYXLyqok2uwgmT%2F16jDk2olNFzNjQm8u4urKrFvm0d6VRixKRWUzOqruDHtCYVvks5R5SNbzOwJNotmO0umUOGRA2%2ByvRofIsjaGLN2KFiDGgCI%2By3tGnYz3wAXj8%2ByHev0xoZlSJMfUF0g%2FQfuHQWGTfMtZ2tNMCcmtBcgov0JE31tHFpzDrlQskwRsQC1ICurQ33EbOMlXFSSJYZmgVfw1ygci%2BuF%2BT8KJb7QIrQmD6vMsw1DB21XoqoLhRnoZuYirrclb69ehf8VIllOk7lliaLO2GnEFEJJSfpIIQZtJjaciP8Z1K6DQhERYToNLRG%2BZuZeIw9owHSC6JTrWxZi0m8421KTQJwOy641vH6QPuTt75jesIW70DoR7U0jrwDFzeDCzr4pLADw2mqYZ1Ah0YDK7%2FEs0EHGf81oVnvVCpvjAfpfPx6zFUxJWClpRrmNAFgQpPlNGRHGmwsbsVliPZMUWyzCvqnjHavh4kMZcE6cJmc%2F3EhrnfN1Y%2FcNfAS%2Bfg8bjWSF3YNVoYR%2FfBFkpW9ShYycTBxv3BrXTWeFh9xiZuMwfX30RmgTORm51%2FPKr47pejpxGHDRMillKUlo9DgHDz87dx3mdE1CwpKDO2OJTeBV6%2BZI1jf9xrxUQ6UeamlfMViZ7o6O1%2FK38Uhq%2B2Ye%2FKuCckaPXsduSg5YgFFRhd5IXS7X%2Fs5mVN0tkXnx7Pd45IlbgSluFW%2Fb5Wz%2Fmid2joroEUTuNUL1LEXT5dv8LRF21tAgUvuDQmo3zqhLzRcjh5uu%2FwAZ4zaZFqlkLwVYkbz0G8kY%2FZeNnJnPF4S7dkUZM62oER6eAMsu8TiXRf72DvUrV6v5j8fa4LvPZ1H4iBBILfDw%2FA5DBy4Y19CF%2FjZb5b7GPa%2FNIVG6JS4avBVLeymoRfYtCdwIGMl7SMCF4XxZ%2BD6dExq3s59YDYLJ%2BgQLi24msCoSrB2hQrCI7EnXhUNkE8M4USsY4FxZC41fMknCCMm6Rn0%2FLWwcl7zAQmwARC6irY%2F3wunuydiMJKGIiHUT%2BtBkx6JZaQvpU2cCR9lCFr7IkWMIz3hVrXZpfviUMNy6dqZDGq%2BgB262pdzZHdlkL6HkSb%2BKR95NH9rVyPI2BCok%2FE4HRP5l7hZX30S%2BfkABPI2xtYk2E9tW%2FVa%2BAQ5rzgMLyy%2FIccgFeIVzDyiHHhaxH%2BwG9%2F%2BZe%2BN59%2Fejl3xkbltc48w%2FW6fPB8%2BUJsmX6bxQeHaX1Q3l3JEa7RIb3FjdgJEaY733ppztyHnC25Am6gKKDhe9yO4ws%2BEYhV000EeG01FO%2FtnDMTfeSbxWAQ%2FueQI2YpcLrLKeAYkstHFPF3LIdsmobw%2FuQJ%2F%2BobZYWwurmbPV0OYd%2F2qlCSU0BBDS5qJPZ%2Blq2AbXEExVt6FygVQHTgDYgd65N6DEdBXHbSrVBRj09PjUbl5KTpN0YcikytAkMOlBkVQEbX2NvaBYh7nmvrreCoV42U1M7zSCO9lUC9g83PqtPIHtEaclxoqb%2Bghb4K4LBlMpMnptuosKA8pYB%2F6G%2F7i0k%2FrXKeymEriotV2S5wkug%2Bz0gPZn7byxAXwbEVHnZT1CAHK2ZyQ81%2BK8SAphtoHANRaoL2JWtanbjkqwq4VNqYpT%2BsDwoI%2FPR955Bv0Rx2IImDsXWgj2P8%2F%2FNwxP6Xi8ifaPDre2edZDTukTaZ2vYUeHK%2FjzyYYlGXEzmZCFDiJoYpBatUZqiB0IcQWfO0lGt0O%2BvjhnjF1wgh4rtTtRYd2OyWOcO3xD1EuH9QbUib5Tc2EWOpIfI87ewC64WOEzweajEZaV4C%2F2LFCEcHg16lMon%2FDFuIslSRRBCVvKvTpdBfNq%2BRs9B8sle5jezXG5SEkd1T9R%2BQ7ZkAQ8egmtTaO%2BE3l7WNs6Itp%2FHWVEp974ngnRaeiKsmE72xcSooaPhrpZKoBje9AHP7mt3UPxnjlHqMEsqPJj3oIRBzjh3sLL2U3pHJmU262xhkS9n%2FYn4lWofVTXEHTNGkE3K3EH9eh6wpMd%2Bk7AjsqTDutNHfH3KpXIgz4xNTUlKgeTA3qhpxWnnFH1G21kIUaaIBxNQLDbanUMFG4X8aGNkL2hTVhQVBBNqodqQTEa25%2BOEM%2F8dkjP%2BDJiUnS6ccREzwo03POT2RRciRqkMFApf0%2BB%2FyskWVArS0L3PafJiuuWnja%2BzGlu3qJ50MalR25YAs9nGqt6%2FvTxNrpQigGTiXfjiN4dWD%2FIVst8SvNyOjxmG6SDr5IPUhBXfZfEwc2GBZfWJqxRHxr0E7mK0r6uijHg1Qh1wbgkCVTTthpaxOaYzNIvYos8G%2BZe%2BXjxt6pdBiVWnas7mnSwlxSLQzTy%2FnVsO%2Fh32E1l8mEsAqDNTHKgTofTuheFbZGFfBcTaD0f1hG%2BilsMkJQAw%2FydvBriyYGXIFDxeStXvhI8xvIuisvporo5vkr4mgsCkcegOef2ZMtJ4QwhbB4xkJB3%2B0P5yNFuzt%2FT8GCNggxpj7fo8aDCMSNt0YW%2BPijIwXjTToFoytULgPOnCzwPl9BWU3pojMss%2FD7Ru8sNY3H9o9U1600%2BFdWFfbm9I%2FXRHN2f4HxNsiriIWeydG4BCK9Upj0g47yQg3GytDzKih%2FlN89wU25u0%2BakoAzYcvXFwwe0QsaAekHqi0UAwcJLRVGyOglGOzjxBpZ5kFo6ijSOEQW%2FRqKyl%2Fl%2FTNhOIjY8LhZLi7kMvzdrOyFTGvAI%2B4EKwMkD%2F%2FxND4jJgVMoBY3PknODA2AChWCLiC%2BDh7OcPbntEO1PtMi9gkoU5ZrsGjlvD0I4oaqcOVdruit03Nh8t46pxZS57QVewefmuOZQtExAz33YNiBQJ3Rh0wmbMEZHJUgUu0IpQyq3atm7sjrhZ%2FRxvFFScgXQYaeyeNPeQmcxqE7WEqmXyVIzFmZo9xKst0R9GAe0MwdGQteV%2Bva1TzTbQIjZr0nfl7W26%2FjEcpejgsf9v3dlFoxo%2BdTv3UK9KHgH%2BF5qiJvQBpl08yL06JK4fi%2FF1Fc5fFizw1gfH3YSjzr3ILOnDvtPK%2Bbi2mDYvAD17rteor40d3Yn7W%2FgfkByJ3r6AXbrE7C9gVJw1MCNw5LBaHp5qwMmCGBDRDMOagpb0nJ6pvZZ6rT3iED3jJzcjXJQK5Vqbwoy1YmOPmxbOziOUUtSIascQnkNXOsR3EWuuSGzQZN299ipBRlTMASbkwvTioCwx%2BRFo0QSu49sCVfWIsyInT7N%2BkwQzGheXajlhNBsT8RNvHfUCe9qy8XTulcf4pvEY6KT8C2xu3Q48rlGJ1NoATK2%2FwghVLbZJkxc0jo7KJtJeijZpxunCvtiUqI%2FWz0eiqCzoyPo7DxHn5YmEuzqCCIfdG3EyvV%2F5rFA61svmElA7eF6pu2UzjqZlk84mo1qYVjFdI5ntjlo9sOQ%2FnPa8VUVSNBEiP%2B4dX7xdzmJTHYmlBf6lBNQLuhfES8TfudES6%2BjSogeZF2j5oEYFWC%2B8PBfqJKl8cIUWmC0lSGljfTzz1XD4kmY0hV4nOiTPwMz3zTsPoSApDVlG6eU8NM4JAK6CsqkwxkORt2uUUpL20jdETuDb5btMzkrPHU83RiHzDJ5JemUOSkr8TSirxE%2FmcsfvY67Lh0D%2FqOF2K2urVYdCepN59xz0C%2BajFgvdYxeSPZ5QSQethS64Lrhk10ObqRWuQXk7ljavCeQX8d8ao9RtGV359A5nHCOE%2BDeQ4%2F8tdRZMLCESdFe4zT%2B%2BdO8dXHciG%2F3DJxr3yREi4jig0uYT%2Bpyw8%2Ff6D30H8Ifa%2FhYocGNCYR3Ym4BMykm5MAIDDhDB9ZhVlatSON4rmMAZOengHoMp9Mn%2Ftfhq2HUjHjo25qNHq%2FlJCp5kXIrzwUr5wWTzbkCG34Gw8OdsnHl5o5QCQqSMXpocG%2Bt0%2BkXhnDHZ3ilnEOQbuK8DPsaabUN52qY3DHMpx2Ah91JaNywFgnbLlHy3oPB0DUHQ%2FuSCMOQgCMKkW%2Byj9mq8CsSKhA3vWOfAz%2FX2B3TOD2S8pTKVJVkVqssxtMDRtGU6AaDYH4a06TvCoPAaPqGNwYCqelqOSdol4NH2JvLGjlVXgeu4148Ws6u4ZBe6TKOUtpk%2BxYuRquY7XzCM1UFTAfD%2BI5DBGJ8B6aXHXYwt%2BK45E7XE1HvYnNV6kzeaTjAQ%2FwSzOsT8DLpvlnrub07HTb3QlbHk1xpvnz%2B1nVOcoaKCxUPXPmPTS%2F%2BFWkAwVyOI7p1v1y3GhvsRmc9C5IAqS%2FpuXfy%2BX8BpKx79dxedi9ygFTIrR6mucjCnoZqFZ9ELbyIE64Zk5GKmznBVMxWiuxlXTm7EggcqawUrCTfK3zqYXprspP0spxJ%2BQkYCbUz9GUDhwwdOaYqz8IVO%2FJh4egjmnSh6nsnqwvHNE1T1oGd5gdl5X6Rl1fZUYAlaXpbU%2BuuMkTMG8LMr7O0Flp3WqXaHt1S9JkTN5Mus1hMES1meavuCHM2fSFvLM35XYWi4fihTo9N%2B78VmypRdh0DA8Myi4sr8o%2Fn%2Ba%2BlWef0SQSpAKgS3HIc0wc76T7NdLiJKOhMj8MQNFmnTJPMgORqLgac%2BoAO9eurzYoRPS4fF5zsqlG8pktKc4P1vEtvrlHNmtUIIJQYtWJsdrXfpZkc5xI5PFymUwumyStJtaUXotXrc9wnEtmevLPtUcRK1j6hgeW796Kq9Zwb4%2F0mfS',
        '__EVENTVALIDATION':'5aUFq4O57IEY88miNmx%2FvYAr1B3WNWUFzDxobfWcMTzbXpqOmqjKcHzAeplckWudn1yMMgbvrEsKoc08KVHWYQjpgDwommpv4qJxr94Iq4EZFzGpg0rvcBI%2FFPRt1%2FwvKbDXssH897Fqer%2FYTv1YQpXzIr1EJFM5JcIw%2BUvqzUUryAk8jv9zGZEi2JMuoaG%2BoAzr21BVkjBcfz4Jx5LGT4zduKLFmtkzHtD%2By5g4gbn35XhlVTnRG1KE5pMscWzW2Peqomaks4dBbRtPk%2BgZ8VpMKb8kO4SjqKrJYSDI318eCgjSWHbc13SAuU6YTPkEnvxQl3EgMIQqg%2FN9ni6tXT1gshdTXJYfdO1aORf2291HqvhkktE3%2B5icRx9c95WCBvzJQyTIf79hJ6y1ZH4%2BZr2DZuAG5I7CZktK%2FyfJ3XwlGUWUh2Eha%2BaFwHy5yxSlEHCFdZGfEYhxTX1yfRSmRZ0sJBrbow9Naq%2Fhpc6hK7ErHyQGrCjrcTRZ3Fwkx6sTs%2Bg1WxRK1eYoIzkfLoAH9%2BVOt4Tgad3p8hqIgqip%2Bv0XVN6x7sSTZi8IW6StXRCpYBx9Gi7yhD%2F%2FhLIQ%2FPwGHMwg1C4o%2F8MUxPVgSBZ61xZCawVddtX7nLdW%2F5D4s%2BOjCGK8m0AdZDL93IMfc%2FyZS4BjN9GMNYL2ZB7felfjOH%2Buvmii5u8aygUOe%2FZB1px3rE13%2FSDuMvvhUCs%2BJqG2nm2Yv%2BRprJSV6PhcQAaFjuqzC9qkZkKKaYIOL7lu31rFDzREv60VuNTVC9FPXoOboj3pCbAcF08SCPWDVBYgGkM5sId78xdF0ULRxVXrk9Wsg9%2B9FeDJBXprjNJspprewCsNuu%2BBt4OkF3VsmUTS7S%2BUNBlWqFUhrSR3wQiTBdOGK6Es9K9%2F2OH%2Flu3YSjZ6tdMrExDoSrfFohqIjoCHHR4CWaMDWy%2BEiciWPUqIgLrGwowkZN94f21v%2Br9GTh6zNBRVXfHTNrAStgRTPhE7rzPaVrKS5wz9EsSfvjAT7bWZip%2FdH2VYoPD7Fj3O2rbOAF2vVFve9AcyYvJTK8s6jnyeErj985CoEYtNKL2LXRbeAlG8Ef4Y2qnnrsKFRMNLy9HWL7rUKYhoAz8J8KbCfalnOEvI%2BUSCbcq%2FbSiehc%2F6BxX3sJ0HW0DdcjSGH9Aca97EOTXUsltztaD6H5rXuFNV9nLjutDctBqt6jZWfpxVmLKsfiSqod8rcyP6ByjJEsvuOUt43svTl96T2nrxlWaUX2dD3bk%2FxEAcQfmMwVL%2BkYdtSGqBzFpgWV810Ft0IFHxqodGqJst73ZUq%2FkK3TYTsniv3gdx9mNGiJCxPW12eflFGCq%2BKUwasbt5GZzzRWJOcQbe1pka2nEjHOY%2FuLtkD4PdoLt7g7pOExVUfuFKitgMVpECRdksIbOSMdDZWH%2Fb8vfCaAO96HOlx7q4Df43PESCseOWiBE2LAR35Y5bjFx7105k7lS9vY%2FzWQeJFEJkd%2BUth2R7WLgsSVH2kqLg%2F5kZStfa1mkBWnclsSudsh%2BRuA3q7PsSd2Qw37N0IGepbCbT9mc38i1FwpuZY79af20eU5oVdvNN4VZkXDhDjdpJubLvRPCLSE%2FOSy1A%2FLo2OKJ6CE7mE7N60rc8nEk51ykvb2mHw8URGBuWeeA1xRo%2B2Eb3mESg12ZtCRiONbL0JLBuPfhgXzs0Zg3z%2By2HFgYGEENIaGE9jayajNS0lPfz5MNt5PKBqTlxeiKTCApNBR2TLzoJmOTKLL28i1UHmzZsa2BE7%2BWNixTbOaUt4hdDXVGTlP8LegNZGL2fEprRhj385o66OaJb2gPJwqoLXRZPaYxfAt3mOz2tALL5%2B%2F1lqhzcn4bTtLGe3wUG54AACrDz0200%2FizE5i%2BRVCxLxs9%2FfqpigEMomOHx4Q2O4Xm%2F2mwLelSg6BrxVAiSRko71WZNRgenvIw99iGr1Kvc9qysi2JDNWe29D%2Bh3yOvuMoOjVzrcsZFhn5r8dSK5seG0YjJEm%2Fppp%2Fhtja2n1bbGMh7G0h7T6kbgbI5mIYDs6FZPtbvIG2FNKTJdRVRhlZtguebG9qCaAomTvVACiNjmu1prCkS%2BQ9SXATdZkpurzsxl9EYEljnQDUN45a4tmYNhWsRhfUtlNjkuuQYgPJr5C8BzTsmTtM7DO%2Fcwq46C7wGHvAWRu8bFGgZ0rit6yqkJ05zLQGIGwnS%2F86zi4a17IKeI1YQRmQNBWzB9aHd2SovbavRvz%2Fr%2BcNZ4SKtpA2188pp%2FcFyNsRwGTfj9IVRISlDLYlWJBWbmM%2B%2BJTLd8NdCd7Jh0xXoXxBqxBtKi%2FUVOuEf1ykezzvWN3cmBUJBRQVW3SgMeykSHofGX7pCdRRAxmXKeAx6WvTaBqtDJEUAyP4wgZ%2BzEH4Ky6sCPfYOiPW3HrNkrTx%2FnEFnme0lij54TtPIQOdPdOZ1fNxEr1LTHViD5v79YLxPxyL11NctyGI2gATYJJ2ZQB5KOzlkakxsTM2sqaUdYJiiE%2BfOFR2lgeV7SdvnDeg2QkoO7PCHGhL%2FIm9q%2FStIa4956%2Bb%2Bh9AqS%2B49Va%2FDQX4bw8DJu7gHgS7dC%2FI901QJ5TNft3xdwVeWL0VwwJXb3AA2GZRKOiHHT6nEFGa25NyZ%2BJS3jldqrZm7AuFyPGNt3SHpjD7Oeon8xxTcajZlB47EXblA0Eb2FNzK348NXnEFFQfrwwTiSCCSmIp%2BwbOBuK7oLWvxn1J1tvu7HADMMbM3An3nMvb8rV5vRrQQMCD1AT5sERv9VyfMivi5o9%2BGc0Nb0L3iEJWvwzdkpu%2BcgDOiQay8jU6k1CP03KoZWA2xLYdX3wTDk5WbjduGolNe1x57wfWBzhoqIJNx3Uc5Ovibg3Di%2FlWZDRtWEkUgWQLTdKqi%2FvV8%2FcLhIOYIClRVLVCh1ZLZUUypYeTtyR18jUz8zgRAHnocv3sIRMoIkIjp5aYx%2Bk1NXiFtyJVVVMm7yXL4UBSPIn%2FxjkhivJiOysHLb%2FzI%2FmkZtJIlK7aAA4ezf5i0hMkPFg2ZvVqdskzTt08VG9yKxyKN7kPrlXimNNl0qA2Ay8EiQURQmAeZpfajD0YZfmBVaA35RKH9CUS1764yj7zWF8KTnNynYOXLvj%2FXhjPNGOIoKmmGl0na5shK4dHWDDEVwXtdtFX55Vj83XFuZUBSQZlK%2FHNg%2Fsad%2FQq7VJuPE1RSkCztlbkKDP1vau6jl4ZgNcKH7pPRo1Xxdperdz3IqNnlW%2Fk6FVDT4NydYqIoJXxrpsnB6KjoIjJGZ8WKGiKbiOPu8kJt5aCP6wh82Q%2FloqsOXgimVCajDc27mbvLHEnVJGAhVbDb5ktGtVVbgzY5YsZNwuY5RaoQPniO5mKc5LHQLCn8oQ%2B7fz2RM3yL%2BFstC4QP7zZQ87UrmmSk0HF5Cw85tAvz26SYgyl9LGnaOR0nmXhoXMGFBFbOuMsrzG6%2FSO99SfQZPPA%2B81PNlU5R8nFjx3z%2Btcj4%2FewJWekgL9r87dDWEVaSg7uwLtkKZQANWtXtggfZlYTb5%2BA%2F7zqiHwABHa3gEqaRP24lMB33eIDAyXR3%2B4k78sVAmydDWoYV7QCdDkWDVhG9cNNB7DTRHaTp8tlwu03j5APTbh%2FN04un%2FMBNRzSw9ykSRn1y1%2B%2Fkmbxm4Dbew1rdwMLDV4gtsW2a%2FMF2wixxDP34hytgBZpt73w8vhy%2F1IqPjun8Z7K7JdIAG72JNTp1y91260xYl3iMio1juOKesa5NiJjC3CXEwyDwNFWx3GPK8420bQb%2BZcIGA1L2u68TbaY6Q8K8m39tLh3cNQl4ofoIKmwcMvy3sScU9O0eXvd8YLiu95Qgh329O127rHywp9wv26T1C7yAvEjgFGyBQmuLHXjdpewz%2B%2BT02oLFtW60or0Bq4W96Ct2kI2goY68mBQbMFK4X4cTVfcV5CxxavkbhEtKqzF7ggvk4Re9udJQMMnYtas6aVSgcdIurxvVEUeE3ggpYP72juU9X5qvzXE5mVit75%2BMVLiE68U%2FStnx%2BSV%2BxWaSeg59FBaECcg9xBaGUCxBWtXhdGAoUZSbd8BOLoQCzY5XRdZXFQXYSNYXkjxKMgqu8a2l3TDtjFgUb8MfdGn%2BVRIN1T4HbpbhjpDKwhHBpDDxDFJQKhDc2EF5EChBtmvHYe3no%2FQK40sO9OaRHJb6P7R9o47obFJtKv3V6iNKnxnRwmO6x3%2BavY5qVmEvsIcW8hQOw3IPuSpuTJLRtX1yHn4chON4CLUvt9fkRiQfNUWmQ0cKEIn9i7PpOHlq2N16dd54T95TJsfMmFb1L57MnReS6dN7a3R%2BFiwoNzGG1jLA8XCop5kuVHmj2u6ujtURBJnf%2F9%2FNmjnzbebP7hZTA2hrG7kXXNk5T0UnOTrvkjve4ZCcaLqSxrQ2gvxzxcHsgnE8FNQOAKmbuDxsKQG%2BSAJaMElzDL3KMkO9njAiAKAGSkSrqOyxJlF6sl5PtjgWSgGOx66OiWP%2FJgcLm8UacD3uwMEcaZriMu5mXX7EFhFCX3Wi%2FrOQwOgK0j4P5dNqHX5cVG6zwvgjsAmvBSAz4kmlk%2FhrepOC8mHvAlh7cKrO0B2c39UQiBCNjWmfc%2FephLwvWBFfkdvhaJq%2F09Lx6tNqPLAOwXKxinr%2BNK9R4Isy3Hw%2BfhRya%2F2K5UHbjeNcyfYD4RZZaWEyEEIU4GBUKuOV0faoiPlE5oJO0bLYVvIYP9WKggKs395ZW0Tn8wfmv1HLOH%2BOlmWr%2FZ7hjgG4%2BWr4ssbuQlweChcynHusus8acB194CBXQmmvcZSgqLU0meGjGFM0iTNMNj3WL%2BETYK6e8uki07Qpc%2Fq9YQ%2FWhyJgFGQ7ATp3fEBIkp2%2BMajPvJXUpZJM4yYQ4NkyarBDC9izCTwCJxLKiLx9WaP%2Fia%2BJl6iajcKraKDzd7APsEMnRlBPXArZU%2Be5MA6alApPYFmfVm08jogSxa6xm%2FQgU9H91oz%2BOV9X227opQNlatMkC9GNFPcmQVhiY1sYvjceWK08bol9AhgAOPQb1DnOANupxR6%2FTSA7GpK9xuduIgpZxjHUCthvW%2BhDg9%2Ba8HIYcsmuYVLhP0vPyY7Qm%2Bj9CNzHMOaAgpLTmBzdakMhyE1Tpq7dZ7uZKC0fYHlogZfAEoBKC3nV71v9kai3vrBi2i6v8uvRnyciuzYysbU3nWTX0S3YSG%2BBRCAADRC3J9icU1SUXnIrKjtDFDa%2B5FeeZPHKzGjsgW0%2BB4cbXm3mC5SFwkzRDEQKntUUlFA3gkYT39qSRKhdxfIpeuq6nijQWdtd9nhn%2FymxW43Cgpq3JuDsAqBu%2FCuCGeN2XPgVJ%2FJEgHOjwcSncIl7771Ax1vV5RnkJdKGXC4fScDgazzBcjw5duLnUbB7oC1zOmzwcIw2Bac3Y2CrerAULR3uJ3Db6rJmgnm1gt1sbtn2EUOpAd4aMf%2FokkqlDfEC1FtWYA%3D%3D',
    }.items())
    return requests.post(url, headers=headers, data=data)

def _extract_results(html, year, season):
    from bs4 import BeautifulSoup
    offerings = []
    soup = BeautifulSoup(html, 'html.parser').find_all(id='searchResultsPanel')[0]
    soup = soup.find_all('div', recursive=False)[1].find_all('table', limit=1)[0]
    for row in soup.find_all('tr', recursive=False):
        tds = row.find_all('td', recursive=False)
        if not tds:
            continue
        department, number, section = _extract_text(tds[1]).split()
        title = _extract_text(tds[2])
        units = _extract_text(tds[3])
        instructors = (tag['title'] for tag in tds[4].find_all('abbr'))
        meetings = []
        for tr in tds[5].find_all('tr'):
            meetings.append(Meeting(*(_extract_text(tag) for tag in tr.find_all('td'))))
        core = list(set(_extract_text(tag) for tag in tds[6].find_all('abbr')))
        if not core:
            core = []
        seats = _extract_text(tds[7])
        enrolled = _extract_text(tds[8])
        reserved = _extract_text(tds[9])
        reserved_open = _extract_text(tds[10])
        waitlisted = _extract_text(tds[11])
        offerings.append(Offering(year, season, department, number, section, title, units, instructors, meetings, core, seats, enrolled, reserved, reserved_open, waitlisted))
    return offerings

def to_semester(year, season):
    if season.lower() == 'fall':
        return '{}01'.format(int(year) + 1)
    elif season.lower() == 'spring':
        return '{}02'.format(year)
    elif season.lower() == 'summer':
        return '{}03'.format(year)

def to_year_season(semester):
    year = semester[:4]
    season = semester[4:]
    if season == '01':
        return str(int(year) - 1), 'fall'
    elif season == '02':
        return year, 'spring'
    elif season == '03':
        return year, 'summer'

def get_data_from_web(semester):
    year, season = to_year_season(semester)
    response = _request_counts(semester).text.split('|')
    if response[2] != '':
        print('Request to Course Counts resulted in status code {}; quitting.'.format(response[2]))
        exit(1)
    return _extract_results(response[7], year, season)

def get_data_from_file():
    offerings = []
    with open(join_path(dirname(__file__), DATA_FILE)) as fd:
        fd.readline()
        for offering in csv_reader(fd, delimiter='\t', quoting=QUOTE_NONE):
            year, season, department, number, section, title, units, instructors, meetings, core, seats, enrolled, reserved, reserved_open, waitlisted = offering
            instructors = tuple(instructor.strip() for instructor in instructors.split(';'))
            meetings = tuple(Meeting.from_string(meeting) for meeting in meetings.split(';'))
            core = core.split(';')
            offerings.append(Offering(year, season, department, number, section, title, units, instructors, meetings, core, seats, enrolled, reserved, reserved_open, waitlisted))
    return offerings

def parse_args():
    arg_parser = ArgumentParser()
    group = arg_parser.add_argument_group('semester filters')
    group.add_argument('--year', type=int)
    group.add_argument('--season', choices=('fall', 'spring', 'summer'))
    group.add_argument('--semester', type=int)
    group.add_argument('--before-semester', type=int)
    group.add_argument('--after-semester', type=int)
    group = arg_parser.add_argument_group('academic filters')
    group.add_argument('--department')
    group.add_argument('--department-code')
    group.add_argument('--number', type=int)
    group.add_argument('--min-number', type=int)
    group.add_argument('--max-number', type=int)
    group.add_argument('--title')
    group.add_argument('--units', type=int)
    group.add_argument('--min-units', type=int)
    group.add_argument('--max-units', type=int)
    group.add_argument('--instructor')
    group.add_argument('--core')
    group = arg_parser.add_argument_group('meeting filters')
    group.add_argument('--time')
    group.add_argument('--day')
    group.add_argument('--building')
    group.add_argument('--room')
    group = arg_parser.add_argument_group('enrollment filters')
    group.add_argument('--open', action='store_true', default=False)
    group = arg_parser.add_argument_group('data source options').add_mutually_exclusive_group()
    group.add_argument('--web', dest='web', action='store_true', default=False)
    group.add_argument('--file', dest='web', action='store_false', default=True)
    group = arg_parser.add_argument_group('output options')
    group.add_argument('--header', action='store_true', default=False)
    group = arg_parser.add_argument_group('maintenance options')
    group.add_argument('--update', action='store_true', default=False)
    args = arg_parser.parse_args()
    for attr in ('year', 'semester', 'before_semester', 'after_semester', 'number', 'min_number', 'max_number', 'units', 'min_units', 'max_units'):
        if getattr(args, attr):
            setattr(args, attr, str(getattr(args, attr)))
    for attr in ('semester', 'before_semester', 'after_semester'):
        if getattr(args, attr) and len(getattr(args, attr)) != 6:
            arg_parser.error('argument --{}: must be in YYYY0S format'.format(attr.replace('_', '-')))
    if args.time:
        try:
            datetime.strptime(args.time.upper(), '%I:%M%p')
        except ValueError:
            arg_parser.error('argument --time: must be in HH:MM[ap]m format')
    if args.web and (args.semester is None and (args.year is None or args.season is None)):
        arg_parser.error('argument --web: must provide specific semester')
    if args.update and args.semester is None:
        arg_parser.error('argument --update: must specify --semester')
    return args

def create_filters(args):
    filters = []
    if args.year:
        filters.append((lambda offering: args.year == offering.year))
    if args.season:
        filters.append((lambda offering: args.season.lower() == offering.season.lower()))
    if args.semester:
        filters.append((lambda offering: args.semester == offering.semester))
    if args.before_semester:
        filters.append((lambda offering: offering.semester < args.before_semester))
    if args.after_semester:
        filters.append((lambda offering: args.after_semester <= offering.semester))
    if args.department:
        filters.append((lambda offering: args.department.lower() == offering.department.lower() or args.department.lower() in DEPARTMENT_ABBRS[offering.department].lower()))
    if args.department_code:
        filters.append((lambda offering: args.department_code.lower() == offering.department.lower()))
    if args.number:
        filters.append((lambda offering: args.number == offering.number))
    if args.min_number:
        filters.append((lambda offering: args.min_number <= offering.number))
    if args.max_number:
        filters.append((lambda offering: args.max_number >= offering.number))
    if args.title:
        filters.append((lambda offering: args.title.lower() in offering.title.lower()))
    if args.units:
        filters.append((lambda offering: args.units == offering.units))
    if args.min_units:
        filters.append((lambda offering: args.min_units <= offering.units))
    if args.max_units:
        filters.append((lambda offering: args.max_units >= offering.units))
    if args.instructor:
        filters.append((lambda offering: any((args.instructor.lower() in instructor.lower()) for instructor in offering.instructors)))
    if args.core:
        filters.append((lambda offering: any((args.core.lower() == core.lower() or args.core.lower()) in CORE_ABBRS[core].lower() for core in offering.core if core)))
    if args.day and args.time:
        if args.day.lower() in DAY_ABBRS:
            args.day = DAY_ABBRS[args.day.lower()]
        filters.append((lambda offering:
            any(
                (args.day.upper() in meeting.days) and
                (meeting.start_time < datetime.strptime(args.time.upper(), '%I:%M%p') < meeting.end_time)
                for meeting in offering.meetings if meeting.days and meeting.start_time)))
    elif args.time:
        filters.append((lambda offering: any((meeting.start_time < datetime.strptime(args.time.upper(), '%I:%M%p') < meeting.end_time) for meeting in offering.meetings if meeting.start_time)))
    elif args.day:
        if args.day.lower() in DAY_ABBRS:
            args.day = DAY_ABBRS[args.day.lower()]
        filters.append((lambda offering: any((args.day.upper() in meeting.days) for meeting in offering.meetings if meeting.days)))
    if args.building:
        filters.append((lambda offering: any((args.building.lower() in meeting.location.lower()) for meeting in offering.meetings if meeting.location)))
    if args.room:
        filters.append((lambda offering: any((args.room.lower() in meeting.location.lower()) for meeting in offering.meetings if meeting.location)))
    if args.open:
        filters.append((lambda offering: offering.enrolled < offering.seats))
    return filters

def get_header():
    return '\t'.join(('year', 'season', 'department', 'number', 'section', 'title', 'units', 'instructors', 'meetings', 'core', 'seats', 'enrolled', 'reserved', 'reserved_open', 'waitlisted'))

def main():
    args = parse_args()
    if args.update:
        offerings = get_data_from_file()
        offerings = list(offering for offering in offerings if offering.semester != args.semester)
        offerings.extend(get_data_from_web(args.semester))
        with open(DATA_FILE, 'w') as fd:
            fd.write(get_header() + '\n')
            for offering in sorted(offerings):
                fd.write(offering.to_tsv_row() + '\n')
    else:
        filters = create_filters(args)
        if args.web:
            if args.semester:
                offerings = get_data_from_web(args.semester)
            else:
                offerings = get_data_from_web(to_semester(args.year, args.season))
        else:
            offerings = get_data_from_file()
        if args.header:
            print(get_header())
        for offering in offerings:
            if all(fn(offering) for fn in filters):
                print(str(offering))

if __name__ == '__main__':
    main()
