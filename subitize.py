#!/usr/bin/env python3

from argparse import ArgumentParser
from csv import reader as csv_reader, QUOTE_NONE
from datetime import datetime
from functools import total_ordering
from os.path import dirname, join as join_path

import requests
from bs4 import BeautifulSoup

DATA_FILE = 'counts.tsv'

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
    'CSLC': 'Comparative Studies in Literature and Culture',
    'COMP': 'Computer Science',
    'CTSJ': 'Critical Theory and Social Justice',
    'CSP': 'Cultural Studies Program',
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
    'LLAS': 'Latino/a and Latin American Studies',
    'LING': 'Linguistics',
    'MATH': 'Mathematics',
    'MUSC': 'Music',
    'MUSA': 'Music Applied Study',
    'PHIL': 'Philosophy',
    'PHAC': 'Physical Activities',
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
        values.append(';'.join(self.instructors))
        values.append(';'.join(str(meeting) for meeting in self.meetings))
        values.append(';'.join(sorted(self.core)))
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
        values.append(';'.join(sorted(self.instructors)))
        values.append(';'.join(str(meeting) for meeting in self.meetings))
        if any(self.core):
            values.append(';'.join(sorted(self.core)))
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
        'tabContainer%24TabPanel1%24ddlSemesters':'201602',
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
        '__VIEWSTATE':'%2Bl6ibaz9IA8tSe%2B21Uvimg0YhyfTkjss55lCy21liWMJVI3KabJ2taQs4GG1oG%2BK2nPfYXg5aaSnyeuWfxode%2FNEsCtoVJtzJTBtCCKija33UFqYesBxAb3nahNlcgZ8Dz1YvGrFsWmYLM7a5kMBHEhqW8IPnz7hks1GogeZz3vdArygl%2FH1VDCy7kHlXkTcds2tFyY0ssM5yaQ3SNBIs8395kmCoUXrBbKFTO8bNvvSaNPR1pWOx9V6EsJe3Ffv3bVwMPJh728jtgBJd0XeLbFLfkfBw6IVJFqslU7G9zC9Qpydwaj15TuHzCckmo87yh2gXSyfmPDJViMLXuYjoNjf52HLJnD4Vltn%2FsfWtoQdxyN20h8FOEtLPmvXLzhJtwh7nNHyGb%2Fhl6W2oyHjfvyTOhPNjvExbtcoJXY9zEN5%2B4IUHHFBxblu0f3nBHnMSvWHPFLWy9qqAktAgomZNQwvUkOcoID3AVzr6LAGoD9bOeXUFKjGqERldpca8PTW3WjquUDQg7XQC5pysuPEdMeR2IFN0cdS2GVuBQvx%2B20W4qr8T4AfxkTMllq8DP6Uh4YkQrIJBZ1%2BCPFmQdRztCy8SB79we0XlAka6Qi%2FDzMgoFKA56ecAb7tocgm7Dq9KM8UVhdOJx5i75OvLeJaAM9ISurwAyypLNsI%2FCU2HCr%2BJe42YznvK46W3%2FuLh3J7tIvX5PnSXV956jZYIZPnn0yCLMBzJN4oBYPhqNqYVEWTOSELOfVuA6S3mds8Jp33sP6ZI%2F5moaP7mNy%2FgvdoGrmnNpQp5oJtqVsJ%2BnXt0iiMDDRJ4eGEIOsqV1xyybUW%2FOp5cGqVkwCS1KhUyM4YF1Xsn3hBqhLFOjWBbQMqGotwTc16PhCqNeTu1xamfHxpjbfiSxIT034aao7CdBF2OPCANAloWVoRflwYinFLV2XY0G%2Bor38HIQbv2y3pOElXGGWq6qY7m5PZCbwdy%2BXugas%2FWuZNh7u9ZFlPoFwHtQm1i2qBHDYQXc9rVeryvD48%2Bp%2BGLcIjFzJ6jwnDgeckRh3PMQEnT1aOC5RYnRYlayd2gduVTADb6xstGDF9ttqQuakO%2BVJp2RuG68uNccDJ4SBt4c4cOvh1KRm683ecAqVuE2C6dw81O6zHSROLm%2BmlExGrr2%2F2yjhPtHM6dbfdMIJRTqe68ZEClfJwAk29ohnnxsQzxU7Oq%2F3GP%2BDRn93kWfpf62%2BA%2FOnkSSEpByxnWaQM2YXnybT9fnBihCdXtmpQ5wFGKkee2iceeNMvk%2F32X05IFTpKfzsq5wwlaK7ZqrMWCHUNFSKzAbdN8nT4VMmbTjAs4GG5pMi10x%2F7xxOGxDQ6PahCDZBdW%2B%2FIpl9NDs67RPy9NYaNbYMzHtsCxlxTDXZQ3Rn%2BSogjgeWxKXPl4xF7SHjAob8iEutqfi4MmhjB4kCMmGOqwuhASPSb2Zsvvlnyv3UXkWoP%2FLc%2FnteIeU2cXJbDsH7KEt6F5a%2Bimf5oFBthhQb0O5EOzKC7bJ%2BLeeifrDPa2WlayjrCFDS06mQ2nFq6FnIb5p4Wvk%2FeWREdvndmVunyfq9ASZoLIsv7I%2BJl43v836zmvfb6k00NzBRyovHjhmuIwyWTosCweJgAUyAegKRsADNhUNkgA%2BsK48SkLLvK5kgcR%2FOtwzehUQxrUWRz8KIo4PIBseX7ekPBiNmzHBjNt6w1%2B8pzu2iDoapiEW9HQuBiPuBZHHH9BqXXLZWzTUrPnIFPdNTwoD3fAz2EHugQ2jTuTN2eHWam5nzTrSwRiOH6jSOVSg0TcczUi1e8jtwyHOE7HfCAZbBYY44Y7r%2BSaF2mdgmH8ecscudPskNaFs9qyE78XFg5BeIfoDavyS2cwBvJakGQHgjDfKiGdJXmzoJitB%2BFQbMLk42kKDGXAwUnnoXb19x2PhXVkd09uocMDRv54SmvQloCL0fYDnnCTxx7Gx5V9jVULnjAzqwn%2BOggAGPxev8N4aso%2BTrySfOaeQ%2FKUqU%2FTSzr9cdwleeKZhBszKad6BMOG19GEVVKpvRWTuWP0BfvBtj62StH%2B9U64G%2F%2BzQhfOpEriyzmJgCuWByVA7I340xieqctwHrcTHHbexL7UKT5pZuE70w%2BWHHhCCJtA92RCRduoJf%2Bya6icQn%2BVmBXaJ2TnzQvD0%2FSdVtYLAxSFGjkRS6TnrEf8C%2B1vQLI%2F8eoE7lAUzCUAT0LDxNL17ZM07VFhyVMigPeav1IOKbPduHKwMmQwG2M6md2piO12eFatzxXRvM6P4Grd19VEuhI51yc8c%2BcLRfSZrXyhSdVmWTBFuEsF%2BLv9zF2IO6nhAocKTcnxQ%2BUXCq8zhmSRzxyK2saBkwaw4bT6cFAq16sU1vv2Otjb%2Bd0tzf%2FUt%2BsfpOBQ9xoDmeV77hsjUB06YG9jK8NU2wRpCYH4R8SGs7u%2FqRCmUj4sO%2B5yElmnJjKwABFIc8BuNd5gPNKrqwxWv1A8MmwlhOEN2SEegYoKgnFRDAG66vs4cxDJKJbpNXXP1lLSsgrhJ9jTvWSpZnwSPJNbKKkRnvtl4UrLKu7cLeq4UZQlvxdB68o%2FjjkJUvFlq4ceFxqcplIxmoU2DMkHAm7UjKNnUZTkpGnW7wTECJrO6m7EFcP6%2FJ9y6wclJhMfT%2BcwrBZiY2sf6JXwDmB%2BsJkbgGSwStrvzVoGALxKXETtQwQ3q2WCo5fbvynWtKi9IapV%2B7KYJEEUSGGMyPFHulxOvaB4fDluwM1aMPH1IepG5XJlIehSI4LEFmc1xW7y5N3jW87Q%2ByY%2FZEbD0odpOKS8QdOGSVXVtqfPZ3MX33R7pc2ISLy4XiXWyh5I4QuXntqPCS1CwdVUrAMXmvlCN81kmCvraMQgLl1CvUySGfC%2FatT7O8e1a7tym%2B57lZHOD%2By%2BRmJE18E49RawARB4FfEM%2FsL0XqwCTzVlFA59XMvuHXMbJ3Z4k6RC%2BIO7th1VdhmiGl4No6%2BAMAXdLe5TajMkV%2BiR%2B5IvDfzqUZ0SN9BV8Z2QxblsalZWHdZw5PHtkQWTkneDS0lXve8996BXVUM%2FS%2F1N7N91xxS6JtH812rRQsARFJw0G2X7aff2HrZvO0fiEWQ9iHy2W%2FyRhp8VcGHX4o5gmfpHzjHb0kLtUGt%2BFfksNb%2FupUgGq4xLFLqNoTwdyJpE%2FoZ3Ws5ajP3B60wUlHSgPMVJbdpwPRjRRVr2tCoz%2FE71KW0zllYQ7c9mNDCDNO4AcY9WdXrwgD8WAzAYnVmJ%2BB%2FscOMdDU0uE3TcbugG0Efn7YyGKBOKSJHsRKZQN%2BrJMDvXCUm%2BUsGn7ThmcyabPUvSDYndb2b1UW5oWmTkuzAwPGgBohfg8IKnALcTaLZimWP4wKAgcKZhi5b%2B0OaTszZo7H0FLPsLZmHe4kje94RC1Yl9J3xtTU4%2BL6n22pjyshhRCB7Pe99czSqqDghXsapKrm3Dm0fb1jMEBbS%2Feg8Tnpm6SDmrkUepJZ8Mw0TNPQf0V7%2BjS8ILHkmgTbQT9rH%2B6NRCUHKEF5UjnqZEiybdNowoLisClcw2e%2B4m0pNdhrhlzhJbXUMmphEUn5sV7kvp%2F8WbUkRLyYDnXsq9LUmHyc6%2BQvHWjSDwmb48xGQA3pVwZ%2BWerHGZzVdbZtioJjDgK3oUzw1WOe50ZCerQ5zP%2BkdHd2FdTIu1EpFLa%2B7KbPpcnN3%2Fg9hJfYY4X2XGXxOFFcHcw76vijhw1FGLYJTM17A9OBTjVGku5p6XB20WN8AgLlKO86pDdx%2FxpOAR8iU361PEUoE5kaawKEh%2BTDwFEMMhXHfzzp7SNZVR9OoVTr2j83RRdigENBjsPKjnV7nPvasuRYldZ3oQsB0%2Bi%2BGacv3%2BIP6JlJMu8IDCOx%2BdxGEceduLg3g%2BO4nCmf3ItyP2Cov7QG81rNKOy5tZoqEsuJu2W7SXzudOBrnGtDsO0Y95tJL%2BpPCvi5MvfgMsw407zN%2B9AXagL4tMr02yY0oT36pzqKYyMyPOWgz3Gh3KJ5ThWRYwSsITsFg7Piksvr8aChH7gYmWhZABJGKkrkwfxGRWFhAF6XxCIhMkZgqytBjEIpx9ko8gA3lkQCPHVvDxKY4UNQq0d89DUcpytTe00Jk5NwtomsRiurO5fCBT0rtt2o%2FxBkyRkdl40fdsmrOw%2BcCExQ%2BAeYjERbxawMlAOA6bxOYyQTKHqisMy1rq6S%2FjUCY95vTBlM3u8mPPlY5Yj8KrEJIZFqj6YqP0PdJGiprLsOACHoP49iFk9Hql55ueG2LvrUXfD6XlUVsBhTKB2UXYPUueFKPfHBFSv5kgDKhklEl9RfUSuQRWvQUNa3oQrgLvTe4rsLAScLrBAVyaPCyMyD6kKA6ykBDY8IEdP4JXWDnbIrAVUSVKy6YoQ6kKj9h9GgprX%2FP1pw0HgIed3uJr9VUd7vDyttsk6IOPIyz7gasZA%2BsQrEfWvXM3N%2Fe6i2K3L4hK8TunxtuPsZrjUOrUYZYXPJqvdZIe%2B%2BprzLOYAZf29T%2Fvd17hp5sRrLUBorff5LyLJ%2FxANYTS4FWD2umRBVWgZA5EZaznE3k24dnpaQ1wTFOO46mBBICN4dHR4wPPw9%2Frl9X46Gyfocc4Xvd28cgU2vp19kIGGO5%2F5DDam%2FJBq0YWEgtqdwh6Vny8Dkf4IkbLAKIcrr6%2Biscv8m6UkZbZMLz3ooX%2FZ6CI1SVkK4y5ipxZ2yVGqhSDpmGTFoCX46Jb1WvtCeqkEYD6oeHQyc9Eu8A8460%2BffAKrhooDt7mKrbcHxtEDCujFGA6ky0dkwKeh6FgCWtNST8u8dDJ4sldaFOuld6TdRmxnejYq2V%2F9XvujCmqgmxkYAK7Nc0rhSR435UsiLbXEZB8J1Nn%2BdGhw2cPnZixDds491o1Hj03H6yB%2BJyCAVdmvelxnQnmM1q7REo9a5LfloG1ws45XBMvaD8a9KR4m7ltGsFWxk1xXD015Hs7XRTviGj8bMRJCvvFIrA1wZ3cO1wqGJarSlqTF5zpZajdAvW%2BaxDQkA57ZtW2Do5neAhljkMOY8ErfhtBfmoved6ZVtEJaBZD7pUh87bfTIlwte8zV%2F3ST2nwbBF4MoBbgSnpaula9IZwAWl%2FH2EzspPRGOQVeC8Sa5izdDNRcmWdKJ2u4IWIwtQnQ4VubbYuA1mX%2B%2Bl1BMmrfxRFucVyMe6TTIBfJ%2BLyJ3%2F%2BakNG%2FjTqursKBfO9Hw3f%2FgB7SVGwqkZwtUZXAXIxw4dBKkruvteWmkL470vBJ7pkAuDM2pDVi3mQfUg1DSoFjEyU%2BYNbVXRjutlB2H8CLbCmNZF15Pef9uPlbPjfowihZRCdJiQFsFnEI9IAVat90SOL%2FVhRAbB44iL3K4qY8g32L%2F7s9HwqQOP1oYt5K3GQsf%2B5JFM39i5yvWRFtsuGDJPVFx4rPOjvZri0BUlEQzKKS3gEPner9S8Q5njCObwDJZ5cbUeoPR81uwXqpCKY4HX1qrxZWl6BapcD7szvpUk8BpZ4cD6i0WhURmMSrYoXlzlMEVIPiOh2zv%2FyIHptjFN%2FFbfxdXRNkhXp6nd%2BStuEublGdZuv76okRBFlFXAXakwChaKXzinRt6dJupNVF20i8%2F3si1zrrA91SSa5RP1wYqFqGCxsAlcybD%2ByA6FYChA4ZHuTv53d3nhdyw2g%2FJH8PTY6ShXy90iTV1Ckjf9gS65363j%2B8GKB3WVR%2B7bBkbqbggNezT3iWcjSMcfw3jGUO2jqq4IJ1n6Pa3gVvO705ci4e1av3YzMJllfhviH1Hj1eKSTmL4y3pK9RZkIj5qPfrNOYJ5GuHHSvgVozJxgn4gphoi%2FRmIcckvelG4GTkRgCRVv49m4N64kl09IlIyfiwu8EAGrxnIioy7qa3BkIrQ1koL6A6GFV07zXupFvPFDcnBoejSC5OS3jE8422c0vqMLXAr9%2F%2BVVIDXlYAlnmEiFsBswT11c1aetEhLmiqD3mut7OVTqH5%2FbZSRc4EAO%2B7shxx08927uCE5F1YVLTId%2BTXEYbZSriHKJKm7UrmacFw1fskMEjGjpflftHqIUfdI%2BY1kMltBT3M%2FoOTWWIASgbekF%2FGH8WLEfE33UU93WHwX1UTnmdk6Nf07v3psauO2st9KvBO3JPCJMw7dKMAwJ%2BG2iPOntuUKYy8nV2zyKLZEJMQvRzbIhBggCPNFI7GwZ1WAtnMfPkT1MzP2TnwQeh6rTaLZQWwdn1aYzxJDBRAWOTfu%2Bdsns8LUDqnwHtzTN1yZC2%2F71oOvojsVElE0lD73xHJP6ih0Oodlnl4JCQ7pKbk2vOHv%2FhEnU61QQJ4SvvXnCSIg8%2FZW%2F5JywWCl%2BqsL8eN48zXlClt3gbkXGcyQ%2BosOdL0hnkBdiBqSqZ9RmiTed6W%2FfDbnL2XPgwV6lG%2BosFOzsF%2B7HVcKWaUz19nKKfwdPs9IbHCkki8mlC3iVuNAi0jtEEANwy7bhcVIAOj9QqWymHcH3rqU3Njv4evlsWNk9ZDo6Hj9gnoodpdUGg0WOiTjcwU%2FaxG%2BkllDop1DwlxX5xKocEgCJQUXU0W0aXWKMS0DYo%2FV58vhw6RQJybk%2Bvy6Xza68%2BCgLmNCZYBfO75zuflKrFMdBN8BXSeuq9rhxn%2BWfROo6weKLC5Z6ixc90STkBp8Rum2XrCeEPgrrUPl6qD2zGGdn1RVg%2Fo1ZMMsk8a%2BIWkWa3ETEEwPPdpbJlWW%2Bxcq8%2F8jcpG3g8C8TzNrXNPsPKbZKPbk3YiKrnkLqmqWNN7cddZx73K8DrPM%2Bg%2Fo9Ewj9fwoiLUroTGzpdrOBUAJMS8IIcfWEblCRFbG2hn7Wt41zEWwnZ%2B2109AlmX7V7NuPQUhsbz8zui%2FxWRPj8CXyv7ANPhtOedPODOjHXU7yOYc6Cnp59hCJpsxPasdS0DG51Wqy5BqhH2kI3ABbFIwP8yc%2F4zmdD5dzzGYfZyX3j%2F%2BHpD1ROM%2FrD3NptEUS0jIWy%2Bbq4HC9tmz7f604ekLWXDjlPiUWXlwb9oflKE6KOuhZq2IaeVYiU5X8HvXk4mqrTp%2BzR5qHI3tavP9W5KrRy5BwW8q9F5lul7iy0bsFqHrcCwMI70jGUwG5NX%2FLZL3%2FxLzfKq6viWzRVFoc4FbeTLrhxsIh5OyMqcFa65V7LVJrWqm%2F9QZmQH1DklTmUb5%2Ff4O%2BGr7%2FHcEAKS%2Fb1u5POq3UbKypp268OiVmHDf6Sx2ecPwzQQrPiNgjI6L7vzWkwSu9K9btNgSrGQHJl4HpSt%2F%2Bx6u3Kq8F7TBrMAkCyPTO5FvfuWUY9kzOohFHOPipb056MTqRCKAG1WszjNDNaodfQZoZwGSUkSkorfcM%2BdWZYgygJrEr2sQKSh8oFXAkvoy0F8sosBj8bJwGKdTanTVsHkBsMIuGtieBZ8ESCrZh2vnv%2Fn8bRHv4Bk1M2wD4ISRFalbvSoo%2F552POgCgkeLFxjcc2Ba4rSPiqSNmAObdetQZ3Nsf%2FrE6NwRr7d80UNrdKcJQIbYn0bIE7I%2F1pElNfhxxBiTlR1AN58VIQvl5dBAU9e8cJsFTBs0QQsDubYr4Wh76yE%2BupX%2FmBiNl1AJe2nfxQZPP56zIX4EqvTrjGPYgmc8uRlAxoMmrV1cVcpnB0Ytn2KZOXTYxay7h3tHZixG1kR3hW0Z2VLwSzqVzoKCZUmrjB7feT%2BqHc6Pb%2FgYNcpuGEMlxN7y4iVswICPAWHNY6QYTBWx19WTgnGhINz72A4te6Eh2y3L%2Bjf93nKFHz8v5kKwjGQ30KMAB%2BlRx%2Fod66rByfFU%2Fk%2BWA%2FChgsyLrQULHPFa6jCgZ05rCp4x8Ea9AIVFiKZBQaXXt3X1tNkug%2F4nB%2BEuZsPJkXXM8v3H21eF45LuyU4iQIlfUPX6wsgMgP2Ec3hCTipsmIdHkpIHyxIDf086XfqoF9fiT%2FBA6q5991ws%2Fs8xNFPakd94Q14Q%2F4FaS6zNiiU1%2Fe%2Fwn126z3%2BxzXX5R7P8X7lY8vRbWXB9ataFJb0uAGPse%2FzPNfRwES4B9rfOFnmIE6JFivmCAtZVXRsM0i7hdD3DwSTlqj7FSBGPblm8yfW6%2FJGqFWSNT7mEmP0qMqCsF1rLDWtKJUgXjHoHinK8RJUPAiuSuh36VD%2F7owPSA491EoCeI2jvEmE0DL5PqQJZ6uas5YcGeUp7cPwUeqF0Up32Vv1bnerH8hVK0JuVIklWnQOrS2PqnctMwL8vf8kZUS8Jzgp1za1XRKRHFsQTIdg%2B3AcZPSkTUP%2BPl6WOXLGdqHx%2FHILBQaUezCI28VxxjfqglVjLl23aHs3SqJxpHGsV5%2F%2BqAA8mJgSWy%2F7SAjky%2BsGsD1EIDxBUtyoZwZ%2F9ueuPjWqi1Isye0nwe2WGfZaplGXX%2BJ9Wokf5%2Ff4FvXtlf4DRMI3rIJMuXBh4i41G2pjeoyXAJsKzU6HnEKmOfjtJ7FRq6I11SbiK80cBAWU3f5TWjlQw3bxUVG2XFeyix0e4cPW2m5m55qLcxzwR3wfXedhsAwvXwbo4o0E17Pqt8x4GddwSFHla4eZcwAp1LZtIThSCK2wIB9gGGWRlmq7x6D%2Fx%2B6%2BOqFra6APbaEJVGr6Diptybi8vq2rV7xijXkJeV9JQQZWyDjJGD0ykM22lHgs9j6DZraWg8iFK2YCktockbsLejaWrxv%2FpKM5XzPfZRDpTHxhw8bypxDVnoHnvNETBc2uqSN970YL18SFJ5mKAq0MqXOB0JxS8yLOMQ4XDe70iZv5YCp2SKE81FYwEDaReVKZrwheZyZTu5ODgg8n70FIvsGmQy4Af9jZTE%2BoC5JIkuCXnJ%2FOuHjQmY0ED3tCA0JkXCJjZ7iiVhxHVjuy47GUkCy4hQgSb04lPypSuiMBtMXZbeQyR4fsnY1lIchBAj2R8Uh4UYlfY8quYX0Lxq5erZWBclsxmFqcxmS1HJVJcc37kl1ncT9GZpW4qh43EBjkk3EJHJLtoz05PDqzjdqPEKqyuqQ44nzLn80lgvAdVR%2F%2FMVtkfAmNE%2B4VtVQhpnOHtQrFEtZ5NiMobB%2BPRWhdwJ8JvSEgwU0RokGHDDcPQb%2F1VfK4NgQOlXx%2BEL8kn6fYYCdW3t5cpc7mOpVLtRYDkFyYsBbEQ3YojiHIWvv4Hbi0BUBzzLRtdz7ZeUsOsnghJhklHrboZy53GfTnuYqB85jcuqdOMpL%2BEQnIVSJWEWUr8qtzy3d8ctiZ41%2FRLvOE93HrQ3bMpNAPqL0GYhSAV22xIYnOv8Ek8bJo5RVOpGxY9LAxppYUkxyugT1bs1k0h%2FV%2Bi8Rgbumah15a%2BgYAekVtP25vxhx2jQP1UIWHfrPK6t0ymMJ6KfB7OlJy4WYjXEeN75mfO5dSSiX18tydwZH4qiT3eq%2BdkiU8YlZ99DITDy3OlMF5Nslz9FCh44yWeLY09PRqfPYyPk0p%2FE666rmSDGgtfREoOA68tO2jrNz2B2wSAzaLEm8c4bAsMaA%2BF4FvWjullCnBZFCdE63mAIAUOfzmCrfWeEROouPFIL1Kb7pYY%2BznYj9pIAIK2AjZRQqLd8kvwZWluSVXwU7%2FnJs2q%2B%2F0T%2Fb0kNdsKCHveDfY4CU%2FpyZt1U1bK6jWslza5YILrsr0czWUdzxnrhn36I4gfAVq%2By8Gm6NKnT4uh2sS9BjLL%2F0gTPKykAW3FPW0xwGfpplcMAIxwQvgi7N9%2BHvPP9GZ8BjQm5WNh6GRPvRJTfI2%2BTyIZ78O21H3pmWNs3B1M9A1NtmPKh2nK3AiNUjsJX5LJYU3B%2BqvbQABRLfM5ammHiIsOp1Mo%2BV%2F1GMzjWX0qhrTQWTqVbOwVs2nwsqUuZyXiCRowhnQN1gVsXKEx%2B8SVVqQ8h1yuCeQ8tXn4qxbb8g9KZ1vP0XD7tRuUEyW4tMLjZKeELdOO48ZxwZaCpL0TcdLruTOrNsEwzTehQNSJDgYJAL10r1p9B%2BZAxu5KO38JaJ2vRtjGZUMZbJWjCXDK2l8laQdumlaxttmnwXX%2BSIpqe%2BDg30exwoe%2BDtNSHOvncbRqN7wTkzwOj4Sp9DEtlrpADx5RyNtZCcC5kznw9pkvxU8ncA6Dt7W2OUsfrWiUOTNCKLUzVZ3%2BZvfhvABqLkSDtmQZVeTbvOYNzONDtL54wJu3CFsE2r8goZke8Mh3DFnJJaXtmnP%2BAlwKkWDVAxo38CIWSWsDcS9zlIA%2B%2FiyNBUnRhNF9QNlmXUyrFJwB4UKrsfKUVlsQ6Ox0bRk80bgojA9pw%2FLf84rHCGSNo%2FxauyQ1nx0NcS6g17i8fXkydM%2FAWXq%2F4Y%2BtPnFC1FVkHEDI2Q5NpOxem949l77T0VS%2BbQMGcLFwb77kR1PSqZO2Ct19aBkjIZ5lKLSMp5WuYyi9Kn0CH3%2FK%2FY50HUqkAhF%2FOfHjKZJuw%2Bn5ofb8TKuZIwALPAUB0zB1CrzKXW7GxWHXSqRMCpIZDNwkEbuY%2F6R0JnmC3rskAcqKzvNupoexC0CwNbs0Ndhi%2BEGmrlyaeUeYeuS1S3T9F8Uwr3p3SIeHjA9BBOK92cTBGNmIpKoZavJVI3F0ftIbbmgZLkQA6neqQZAaTQuBdXwEfJoTACphYmyJu6leRWr3J89Svx3HBIYsiu94a21f%2F3L6JW8aXyXGvzUPXAYLOLW5kwS8ZKcdiF23bEULkEfNR%2B7AyVI5GtrC7%2B2bCMXLH4dj6dKPdsbtq6LjUwoRS7EEi7IW3DLKoshp%2F1QHm1%2FQ53%2BEfiFeNg%2ByVyOQ%2Fi2I%2FCBf%2FtbAf7pFqM43f%2FECNTC%2FboPSPdOwQkpagbqwIIEegafA6etbkLagr84PUknGDBpM6UXgsjypVcbQhvh50pV6bOXKnNWzTZD7d1D8%2Ba5ShLI%2FqlnDewMggYAv6ekAK%2BOYXlT7vYkP%2BMsk8ImFxAsfx8zHDxT7%2F8%2BFg%2F2KCUYA1FeDfTNBMx3ovq8AUxdE1GcYJbJWkggHT6vBGIjeOpoDkB9BTz16asNEnmDKnBLxJDvjhzj0aUKjK6BJCDRK1tLLJC%2B6F4%2F322uC46Fib9RB6yEg0f4RwrPprcg%2BM8KmIy6lPWhDSOHhxi0aX0FTZ4E3%2FfNCwgNwco1uPuDqn7QG6lMyOkQdulB%2Fv3bSKE1iN5uo%2Bx4YL1FsDQ%2F2a9%2F6exUFpHXFsZA7xFHmCW0lJEwbeVIKz39YAgBYs5rYG8lS7hY03DgFQ%2B6AUhshpFP0Qj1ezmThDPZt2IZvDCFKLfGd%2BS93%2Ftk%2BsWWzJc7m%2F0g7JfJCyMXucLRstc%2F8ZRTTNVsURLZFyNli%2BT3G5IHsz3aDm87tjiep01W3ZUvoXhtkDxz4TZn4NO9n%2B%2BUtj%2BjPvK%2FDeetPfSI6I3514W9448OgujRlOz3iEhQoOKs9rTsjkCD9YKEVy46pyFu1CS2xxGbjM1H10HJLAuI99iIVWxTbZ%2BLH5ws%2B0DiDpEkXILuz5LmW6mMQ660FfZP%2BXdwfq6uqtwiHbMHoqaPTzOxrJql8gTeinvsnfLLiufE5l2nQgZn1bzr9PHUaYnDTaM5rD9M%2ByAQfcq7zAE0Wwo2tqHRdF%2FEYqaCTqKQ1TbqEvVQsNVAvQ2hcc2ZcS7vMfFuBHnm%2BBhd1cKuAuxiEnEnxp4CAybgUHNT0VbCrYV3U5BgA2gUs1tLJcmWv01bzlqKzT3zZi0kNOidEfD27hnhTTDMSCFxf0y5ohfFJhtAlNxjdXfbSv7W8wreVBDWQf6tHCZsXEHheDJqSdbBadccpJjlgvKguzLiLgyT2XHLquaHeKQ%2BDYmQKFq%2B%2Bahv9NTDF%2FWQr%2FigAX8D0qmUhVTL3a4ndkHa%2BHzz3tz1BGcr5a3YukcsowBd6EpNHaYmoa9li6R5DkZ4RaX0%2BqF%2FxUYUkdfbiQVeb%2F5DcjWn2Yw7KPS0cw6wX13GFTQkhkKgF8QWycWb0gMThzjYTPJOvVf7dy4UH5T%2BMCFJ%2B2UBX%2FihGfXEpjQo%2Fy%2FVIpMsb2g0pqWTBSSPAIt7yY9Cw0E3mJln4LQepaaTcf2eSXntbzniDdpzJ5JTVz%2FPlliDxfoQVWtlg69vxhDEFDYlYdCZeKGlZ8W41fDZB0kVECGjLZKbtK%2FICiQUFqXSMvxPDERwbAUTlwloRdMWFFg4crTtAlB1TH5S6fONwGYSZfclh5lQI62XbxrXdNGUfi4gVhqmMQwFtFaCzovSgqCW1PiPfvkxKK8Lpty9WcuhDxT1pqwRu2QGnD8EdgJ%2FpU%2BjVM9eRBRM298ghOM4%2BRK9IcuBY7h7PabY%2BSQPPZB6yZZRBc5aml1sF0r38uFe%2FrdKH5x3nqo2%2FufUbPb08w4iEJT3TMMrI%2FOwM8B1PkBjhbKvIPbpWzetVdrJ1rS6mrVE2kp9VOjK%2FfMpIwY%2FNAsDi03LM5CaebM6tmmNJ5rLCzeFUlobT2kvw5TP2L5IJmYvh%2F8SjI9F2IY34ODMEbkse5AknY%2F%2FBlixJ1C1fAhg%2FrVe0%2BxAwWGN3ivmdVsLFo2wuVerinsZQ4%2BV0YVXpM%2F19QwF%2FGQelEKiCvEHVFwKaooqnDGJHSXwx2WZRbeGTxibC0G2YPzLHKY7KuvY1tGcozjAU1MpgqTgh2Y6mSjD2xfNubmDr5VaVHogajHfflJtS98qt5fhDmcyMcvr9XX%2BZHYuLBclC0Eg4krslc2YXM%2FjslnzlXQQbDZdNyztFlODEdtrYG72irOizPe4h6SqBPPlPRuqkSaw1uIho6H1r4ULydDyXP4hmzLHUkeeQO1NbacCXW7aBi8x%2BfTREGD5rVtB2yO2oRBNzo6V0WBj67EXpMeO7ZCPRth1dGjg2kXSbXy8oGv5Kl2fld1hcc1d%2BLiEwSDEZlwDP2ojKj6CVXB2bnLY2vM6S0vk2YC7ckBdLp6%2FFH7S2GYLyBoOSIPzhL912wJxo4mlAh8JCjWwsRM1ofKIWi6nul11aL8bbvw%2Bbuhc4ganEG%2Bfq15zbgFrZponoTo3w1T%2FVtPiEU8KgCk%2BK1Xh4cqqN3jlZokKEofdvfmZue49y4sJYgwNHJlorbLLn7kXTL04dmji%2BlCNHeATry3qrxTG40Tc3uQye%2BBkkg60rbb6UfxdTPJgqjLtEeYMahUHAQI8CdHtvl1a6MwgC5IW%2B14cxe4Nf2p9xQA8CmT0KLesktLI8R0mkU%2Bg8Nmj88xYd1EQ3yFCMYRYFBpnHKnTMhL6wjvEC9v2nEplYkixZV9w3ceC9wGCPB3Hg457GOx76oPdXx26mdpbVtlLbC0UD1D0ku4RuUc%2BrX%2BdWcl3J7cnOZt%2BjRa9i6byge51TD5csz1EnahJ%2F00sTFvZmWD%2BMCOZpOusLmMG5CM7%2BhSIZuWRpldY5xr6wJDyWRnzNy7AUhZzsv40Fs46RMzWpyyLy1HFmVeGBxHMK7Ju3XfYf9v9TRGPNrnME8EN%2B1JsBVM8Jnf%2BHwviR1WfKiihpMmOZoRsecJTUtqJa3zkeKc3Ml%2FO4VmXR%2FlaAZFN6by%2B4F5a85L9GD8WFVa4Yn1PYO2G80PgHSC7%2FHgpXKnfxsrtJFr1L2WPLmk7eNgxQzkBz7g%2B9Mq9AQRjehRpSyzyiJb9Jru8X3E4LBObH%2BF4z%2BB2V2cN005E0e0KXT3uujhsnJwlxPSTEHF8h6mNwTa0pIc5yXuE8CSrBeagZ2drVUI6aLvz8KzUk02KU9pLsUivJasLwXh3FJylHMczGs1Z8Z65EPrtYUGxmIM6LKAb3RPEYOaDMCneQrF6ilwWPMtOnkQTWbBr7u5I9eHOLLHkm3br7KWJ6OJ8d2KPCBMWRxp7rJVWakyJjkVZA6BN6nauBaVC0sQucVqqxmc1OTZYFk%2FVP9kwZIAoth3SiSLN8wwmyrMaY4XYYGYyr8zEol%2F7sacA6%2Bv5cMZy%2B%2BzXtisDV0YajMFi0pQnV0WL7cdz8F4QaWyq1zoSthKHElLJlIMhrGRQhGxKBjbqMQwh0Lty1aQVnDQZcwBQp9W2ELv1z%2BDGj6soIvik91gxMBGU2PkNs49DjUWWvXcG1nxsgXevSsUB5mCZ4T9%2FZpkaKaBPhm3leZfDCDPDuTLw6Q8756L5FPXdPS2Q8dm%2BzNdI9GVs%2B0kLCooRCnuJ0L5LYd1hTwaLEiSKhjqCXHwAEIgX4lP8G3931SaVo1eOZj86SSnhnL3M6rC1mCD0qBp4VwM0v%2Fc4G9uZrjuuPKl2jaLV5UdBLvVitNZCMLoA37TjFzOP0dcRX6uWdftFehyKtmW1oHORDTOD9AVHMczr6gOOzE30XUIXCdb9IcFUZvHXhE1N60OKsus%2BdCHrS4fAzlMfNxtlYjfqA0BBzwZ0fwXG5c4GxtXN7LuNM%2BoIwA%2FMv%2BCiF60bxDOX8GeUUJ70guMmR1n4Wx9ifnD%2FKlQkyFmG7gDh5Yg3PXL%2FqsuugVWMF25oB3ZVuYvkwkf5woymiiwBtTvi7qB8tywj2RSka7%2B%2FJJai3jOHi%2BLlpoQWFDSciaCpo1ivkHf5ZDJ%2FZyjcAafo2pRsjefI99WKPZ9zL9j9gAxL5cR4x2aeXpCA09cFspnATCVRB6EISBL7SMQtpDQaQQsdjRz98jDuOPNoG7yWr0R8U%2F1E0fwuHvF8%2FKahO6fabmK5Z4e5Ct6P2D%2BLb94oCoP0%2F%2BGnTeby9tUp9uSpcZ%2BAZ1doZvHfhzTfPge4mk7tSuTf432Ljq%2FoVxwWJJvlGbmkJrMi9M%2BpyNLMQvwg8%2BMOc6jzpU4CByydvQk%2BWA9aDi%2BHr9DA79CHgfxXxrWxoztIAt1fs0Jif5s6KjhB6Z9pCyiYdc4X2PKcnt75uqMz0NRNjHuG0y7eVjJVtJyO%2FrfpRb%2B8Yi538rMi%2FTIXztkTruGsd01X%2FKlGtfaQ1GM2djlf2YJ7aWsH1Qk1IqKjJtbwTJGRuCapj0SpewexCXLaQU1HNvSMbv4G2mxtcVG2wQRW7GlkAYpLJpMhXMHwpiNs4taE0YCeaU%2FTJIvqc8d5a0YKOw0Lq7C1w5r9oRSOzrofgDIGrzshEm%2BFKp%2FT8x24oaF74fNUj07%2FPROlQranaz%2BfvWhb7h32CKNsKACUsbIlN8nSWyUj%2BoHfFVfIiJbwbwPG0yz8eE%2FimU25s%2F6JUlZf%2Bf5HHLL290we9t0pJxT0tbtmFRNHXsDjMNkfz55zy%2FWYE3eG2qaIPBWh958FVdNlphfquQUONSunf07YSOA%2Ftf7OU%2FQTOvm8GuLHFPYdAqldBXqeIoeLx23YQ0%2FTsgS5Wjo8jQLRbZ9bKk6j2y1cLoBjvJw3Cd2IoPyH2IU9bp1UKdrg%2BEN5K5KSUQY65hb8YP2%2Fj9VpWrBGQG2%2BXobFXYny7HtYWH6V%2FnCjZPeMjXs%2F9FQW0kuKZJmN%2Bmt53p7E6yegwrRN9a2%2BZgMtGGVYRaBerav0vEjY3cv6yv3m%2FtxtHefMeCIrJOZPUDU2diL2VAGp8iyH%2FT1g17UHJRRDJ%2BGPLghrmCZOrY%2F3S5n7nYo30%2BzKKCm4NjhIzFLSRs%2FOMtQoplX312dKbXUl5wnMHtDSPjTk4PMFrI75rzyVJjwwICHYeabGJeymRtDVQnz2Zwr7r3gV8v9jrpwQwStqQ0fZk%2Bfe8n%2BQ8RPPgggObVu9rBCuk%2B%2FiJ8%2F9CBZPsmXxHWQIpQsX0An22cjoz2BVLAG4EmifEvK%2BAn9c2ZpWebIU%2BxN8LalTLTHO3wRjVF60aLVd6fLhPBwDW9xUjC8f%2FoCw5%2F4RJrSE8MH6c2wdb6%2F16Hbzh7ZU%2Bv7C6AYLqWUdUT1hNUj3QmZadYMIBzXknQMdBpVuYGpuyKyoUYgRpT1%2BWTX2wjidRhzE9ifYaGqYYfkTGVUwBS12sUwJ5s32kNJkeRVc9fWLXFM%2BkFXM0Ep7pgWz2702%2FTUpWZIy%2FCeZN%2FwhtCDmQcSYkYTK%2F1tPoL%2Bvsr9FnQ1Wg8FYus7jHBHOXHdsbPF0HoA%2FLu0D8hZ6MQz7fsck1z%2F6YH1abRORlJq8uVhSVAW6EV%2FvFHYPGan5sIz%2F%2Bi4qY4rtAAFf9ubWZm0HBWnhgMGFWCwRo4PzBeYod42bl%2BRcp7WH%2B3yb2bgWN70vx52B6snPZ%2BeY%2BhKlN5hpz%2Flg3eFPczO4s7Ar6iz3T7%2Fd4%2F7ZRDIf2EymqH6mOXRNb3XwahPnyFEifR7JgDWG1Oq2b1AoCqnECoEDClkigNd%2FaFtIIq%2BhSdSmw9jIrj%2BBTCpbxjsEx2KurSwXdBNCi0boYJTjfMZ8ErMQCC1HXPdDfZidr9iS1yEXqgBnstVM1qusRY2PNZWPSwhVsOFRpgNAVEWzzurwP%2F8qnABGC%2FvyWBruvdrZ8JRLivPamXs%2FZnPeGdKdaKjK0P0p3uv4FbulF%2B%2BEhoX9Mz%2FgNYIyqT72LeCbDMx%2FTumI%2BNXf5B1OoNgCcIx6i9M3zOl1lvRxclwImlEWWV8ubmkllhhG12LGWCyneyazRhNDyt9C0M4wpF7WnhLXi8upAhIOVZEdzFJz7TvSGVY50XUn0YG9tMOkvoUwZs9DTxJNaBRaGww2%2FhNEzvTnjPTaOOPDJh3GMOywAq5%2FYZTKCgh2FWs7wOLxTiQ3wO9vLPbJgzEHTh217tNHLdaT%2FXeh%2FgzSo786xNLSvIwoVCFJRwi1j0uTaZEE5aEHl1tAnXdO9OEy6AWzid9ySAzhMF6jKQxwHDcct2FYujCJtokJq2XAqqDfk3tGVsjh0nhKP6Oa2q6uhuAE3H9fMT5jvwRu%2BcimFgpJOqncpEq7tW8%2FTFv%2BeWr15u2tZeWYSjOZs8%2BTbxAp9J9YuDordtAfC%2B65SQ4otlyRlPKHjJcxFgdHGUN4gtykhpLyF6uuG%2BMasiNcxig3B85VMRjq6%2FJ%2FyhZ%2BUkaZ%2BvVu39mkgBjX5I5JuvB4Wzx%2Fkm8We2OKqrut1%2FwZKbhWxvS2uHcuqcOmVRJmiv74UXBDod01YVexXwW6KC1HzT1RguvAdBcMgExIUK5h9til6r309XYepv08JEuBEF8pK8a%2FZJ8cDtNdFjepliRvRgNcNuL7kxQnYnuP7%2FNjQBzcx0wlPBxPoaZKKaD2aRiCI6PJqX1wP1kKwu9Uf2%2FDefq02YuX3cqS9kB6gUKXLICBe3JsoDs8pW5di7ld9HBcd1y0lC5RI01QHal%2BITHJJIUGGkjl71OmKntQ5ELFmr3AjCdmu%2FN4XnLDnHFY3tH%2ByAJ4LcTCeeytbjWXRHdXVq4rCNn38xzWChG7zn0pp6PIF%2BNkzuRV%2F2yMISqq4PV7pzbPIq%2BCfEkZNXzWToDtPkFHtZ4t%2BkquwVgwAS%2FDVUKUoSZ2hPWIK9vQSVXasJ0sr2CpScFiDwmMroRK5umMtXcE0YDE6rGroiZ5qClXvFo%2Fw4WVQ7hFDHX%2BFeSMPEXAGWWztc%2F%2Bg4AAOgE8lAhDrvRlHzc1Ms4%2BFqAHN0Bd8fLk%2FNJNg%2B8yuSBL0%2B6gZrgBhBXS5ynpS6KZVPlQK%2BN%2BeY7hEFhShBfZ8st8D2UkjvoTNyx24NFRYgZkwHzVh2C02Ps%2Bbleq%2BUiOgkfn2mv6qF0kmsR%2B26ekiOQbgzjV0bDnLEHvJcd7wdG74%2FQBNiPAn3kU6BcMg8X5wUhE1201VE2ou4%2BbuUZc8SDjDf8RMnhBWJsJghxs%2Fy4gfiweAKIbP2QXo9AIPJWJ2J7LNohcMX%2BKTRxjh26NgnJ3GSkxz72jH9XWbHrPEEplVwe0yopEHgNscVTgt7dYgtoKHe84EYBXzB42%2Bk28gVqsUIVwCRllsoEqWjlnMR0PH5eysbwYbYE%2FQ24Wevhr6w6B21tH%2BoUSA9SnmfNwOLg5tmQdRjI9Nuq9awDjRRxmJ9pxCTs9iFgXwoph8XbgiRhScY4WkgM4D1sGREqudxsmRNcyiaU9lbZ%2Bv8ZHhiKW96vOsyNRKqr2%2F1cIab0FwuYg0t3fBt70ZE42LZO4o0wN6wWO6XKE3uVfZHJ7xv%2BbOhXpKxCvvKEjvXLmZgd6WLxlPEn7KtzUOOAdfn%2BEjPdFBQST2bNbQZeKxS%2BzIXVwIA%2BbJ5h%2FDBFG3zST8kD80IAz8YNy%2F3xAvjnWJ3%2FlWdAHUjq0tNFB7hExX4L1QwuvnDsDN7rNaVV4%2BBfny6jzAYqE3id3aUW1yxXlW3tMpRsWq4g1U5a%2BMIJBeVyEu9wecoJr3uX3Yy58VdWvhvRDyQvhQGoICvXP8CvoyLhS9haeKduBcqFuh6Yf1Sy5Ra1FWLQ9pRh2Ja%2FZtThRaQLrEVLQEZWo8bIPAAWNWuAbreemKeehmlTgESzhVE6Amt2dOJeMH1%2BPcStDa1SulF0bGUImVWEH6ipSvHi6OvQuaYRqgUjHX6s1m6TiqC4aaZ7%2BuTjBq7VBG5mClQ2%2FfGATCACXRrKeVVQcpX97YBLe9lDEuaVuOq74l76BD8LpH2yNtHiSiGbg2LJLLWfemvV3SUW1pMudgeXflGYk9hsPcd4UTqqU6b6ApW%2FiFsw8b3nHxIKKhKpl2LkNHjcW4DWtAotBVZ5FJu6OX7UHitA9vVwVd1mqnmxZvqSDPc6iJ1EFfDarZ4PIRk67RtZ7v%2B6JLptsWvWXIPSiFjsAlXjDnsAohUJ7ESQ8C76QReaR74ZmPEotA0qnC2Hd425kgrgZAViuPgV7kTUTH8g25Qd1v99wyOSYqtskbzCt%2Fl0BhZ6ep3q73CqCbPc0rOEvNPE8SwOQsdPDhYnAzSFWlnkb6T20n80Hupvy%2BT766ztRQiLabNJbhMYoSqbkSbg98dIJVJn490Z%2FsJR7JSWFmDIpsON6fMroMX%2FNUkyyw5vDj441AuP%2FtaRENq7jM4u1Dp7RjrYlMt5n8G%2F1xR%2FNJ6kbdJvIk4Ey%2FdsCf8SrIiTVSwVCNuhm9ghye%2Fk%2FO0T8ztKQ7RSPjDo3nNxeUlEbRSQRDw1rDCZU%2BIhScT0OxOk%2Fm%2FtTNEh35EAJtXJTE4PvBPv9SVBIKFXyQ2nzXyxQJv80z%2B%2BWOVgLF0W4VvgEJUUZMkNcKIo18lpHDrpPrvT6ANslVp6RQz50Sq74P%2FeEbweNjkDnlxrlKcxj9PH7b7whEFj7UBGwMll6I%2FZShCpCw4edP0y7EVZGQfuNXpGk2GduysLdaU73hUxRo5YcsKq%2FfehCzUSbQ8g8YBXfeGCPGC6uOBOXCe2igRJsEwm51ieGPXHorAT01SBmLYwsYQVBTkhlxxRFxx7SQHVzdx4xpqeSi4sdtmv%2FfoMxo0WL%2FX4npPrMbTd4tJEfNDitrXhMRttwUUhIds3wWWSPwae1lf8jTnrNBRVqrxzZvyzyxCGU%2FmrDXcKWcPiVXxj99XT28Z91%2FBYM5dbbTtqZX4BNWhPD1Bbug7n5zhNqc%2BnyxYaLn0zF%2FDIrh7j1gJ4lMfqOsr%2BhvYv%2BnLtYSDs1wAghLLtnmkSyxsMKjS%2FtO%2F9GLGhEXi5hVnkzoMGkkXWnWMZScKfvIPYJTrY3SgxZOcra4uKdDf8P6J190k6%2FUkv6Ohr7BVV%2BzM1iv68iNWMsdcJDM%2FqIquRhyOfNn487dKUmMNRIWuCNizrA9gdbgYo6Cvt0GgD6zsLSJVwp2i2hMyHZAZ%2BvFUAIEdbTn3L4hC7fSNZ9LG%2Fuzwa6X0fcIofQeTn%2FOgCNoPfr4PHNDoj4Gm1%2FGPkbXpirSwbhbJ0OZd06xfjid%2FoL93QQ9cIX5NYn6rYA1HIr6WmdC6GtLDgUK0BuVWLJu58eoYyTWCuR2ejNB47cd5TTeobDNbPsbDj3e6ZSvlv8yUHQqwDinYtnizdl1AQ0PK3jnDxluXmFzWbfaYOO53AvLptPda3AYkXf4kScbIdvj38JIvyK2nsD4J7uIieCj9oZ2%2B221%2FjkafwFeg7YEZ4u4Qp9y6hPozCaoFUtQgVSoXOeh7%2FkApXbZ%2FAca%2BCssipr4w0G%2F4kN8H70vgcCL9ugYnegRdmnIIWikIzRicz1Dw0uVovVUL2U6VBRwPIosEenRf5Nsdrz%2B5MaV1cSyQuhdLnqANWt9tAT3n2KDKxgt1fSUsYyXr4wpu0a9yiLgc%2FbS8d3MtN2vG0YfXJMaScF%2FXcE1gBOyZwaqx1UBVOF8GpDDD%2BZTTZLimH5DWBzPqnAKdJjYA%2BqYXvMIHQYnjZePT8gcOQZvdbVY2nkFIPmZEQWI9qA1yWLNG9nqjPgLZmOQH9F2TwtoCpq%2FqqvKfDkFf0IJgNCzn5k%2Buxf4m9rmcMc1lbNsQKmwMIwXq%2Fw%2FOzxhkwi%2FMbs%2FgKw42vRfxgCj%2Fb10G7sP1qIKH5Ykbi5wV348fGd9Z5SCOuvIClIiGg73LWdYUslixzlHJ2d%2BGL6tAomnWepw73jGQ6FilGAn%2FFGzUhlT4w9WTdeaK9cxasHkeOX7pdhRvkwfhuSy8CiBbDuofvsam6%2FAlFVae30d7l4gLDdc2uoPKYdOXiSm8EeTCbmQw0RNCN7W1m3AWW%2FkUMbi8vZ8WQCXvKcrYxK5C1OJhjp5bBGUhVSJ7f0C2ONsW602jEfp%2BgyE2%2BnkKbX5G9vE3u5w5oLYGPDCM4CcBhfQPb1Yl4CGb1l9XFlbItYmF0nxcfOtlNF1He%2BkqHEACaGUHH9J0OuxX3cB1YH5v7YXKZyFeJZ98YIZkIXqEmkwrDMwna91BN7Bq%2Fu%2B8zqce7eM9RJl%2BoirUNTU9nD%2Bobcum7gn2A6K3hwu%2BzabrpKXtHI9X0pBeD4Wze9Jw40%2B7o42e93KTB2V9wBV5bRHeprTg7yNv381XBmu7DNBT0Jcu72vTRiyyXgWBW2IjhdUTet%2F9dBq2W9UzcdTYo4hkuKwxx3QThbEksot%2BjZzkBV0E%2FlcbyQ7Pe33ZP%2BPf%2BvCW99aYIjrq055wETtuVK3etwMdOGvAVMjtRsw1F4anWv65P%2Fj8xweGckpWy28nww03IUyHpXXszZG%2BB4j3Dt3eVlpfCNcCIqSz%2BT5%2BrPxxcDiO%2BAmyKGkrOXgDG2npgQ1a%2Fzsq%2F8QN8ffCjD8eHtC2l1hh48K0vVW6nLqDJXQrr9LBm86TTBVWd96iF%2FYgMAtQiZbzaJUpce911E3F7D7UHPCoED%2FKxvGuyNCrAl02FTjn5ZPMot7J2p%2FZUOh%2FsntdadeLQFMl0WPSo9I%2Batme8BYxyWqTVUJxuEG9ngWrbvbdxTVH5%2B6DjEo8c%2F7P8KHN9qtTo%2B6IQCC%2FW82b678zCPewBRV7w74A%2FJbJ8xiYUHlYugp%2BVxpD9NDbNQwnMSq2h4YBAt%2FUQCHXNLvZ0ihdHhSTMiZ8juZaphShw7amx%2FwST9E1BuPkVZz9vq8NGXEkDHxLuFM%2BWcmJgMHMcz2JDwxFFCMVaf%2BLB%2B5g1qyt7XX8DavCxzv0Ij%2B1gHsT2I3n994zSeyaKAsrJesnfjVoqFj%2BiV5OEJgiacpBYDAQEklu7wo0V7hxOU7jXzgORdzXtd501NDrN%2BdTC80noTeYb3Zj324pFj7JlQZpqnOOvfDOiHp3AKJsJ5u5NMphK62%2Fom3LsD7SomE%2Bqn4wUgVxglEM94CIeUh1lOIIf7TvGYJmKJedSRXoBJtL1niFBuVd6aPwHr5t8gLu4PPTDTyfSAWDHoY97csemcKiufzt5rWr7SHYWzf9hHxdRk1WwB4WEvyJOIjAQyhKKQMpMc646YVHOo5a28r6wi5%2FyKzOdrxcH4El3n4l0CIu0%2Bt90CTcQzKoeCixcjIDUyOnLHEpdXhs2nVZpKsb%2FATiMmMq8NEF9uqXlUBTaqfOjarO2wPhd8GkuBCK%2BMf7n3jTNFpt%2FZKSvlUK9E3Bjs1j3wZFa8JFOoapXFymQqNMo%2BdBpVtySCdYs0WdGy8ZhccW2xKnyWW5Yit%2BNHptt2K4qWm4cuvllHOcvTc%2FSXvJ9KPJCoWNtkpHnOlopINa3qiKq265Bbx0X6N5EPUftqkiYsWn1%2F9ykTG7J3b9dqRC%2FcXiJyH0PlZItYnnXzDi5yHRu1zHSC6%2BBKkzuc2PvIOLHTPla7bMmyLVXCuZOss3FiXaVJ6yZ7yYeZPnKKA8%2B2%2Fy0MqMY3ML093iWXOqp0%2BdQmKxYBw4i8hSTwOL8WMO9RFsQ9hZuSMij4FVwHkH0GYuZaoD%2FDSeIsO1a5LgL4%2BqjnGsoTPlZHkzng%2BRtj5N99go0U1Vl1t1EhKKmMr5SR7hfmUy%2B4SBJIbr2UWdUMr1yVHw0VOIiiSqcfkaWoAwTMzKUiOwC2uUZtkLuCudDpaO7jvBZqj4UNhOofNE7EbpCFtNdfKJ0vj4xVD217uy3ACuGNE3JYaqFKssZvR7SYTUc%2FkE9TbSUWBWlzHUmVdS%2BsFNeLRQi%2FSaQo1rYC3j2LzPbth976XaX6bWhQP8DK1n%2BqWBQofsCazkjeOkYlKXroA87D9%2BIovm0UZCnhkuMrAVmLenKtvXhr%2F9wfA6dZyeUkGajqIjTgoe37aLlZB%2FU4dBcU2yPk1k9XOtOsiLtAKd13lxFLPlioZI%2Br6nO9zhqC1XbTtbLFCMO2uaG24RXoPCBbLKFTNH4CRj6SZkcPeEkJROWJIFopqRHhacM4YhrqxzIoLzCSJI7YI6urNvpmQDLNppK2nAV5Yqe6LG9lGRDyD8mQJqZPO58f6Gt50ldznLF9zm4O%2FyhJxc7bbh23Fdmx9TXlGl53lVCfNq9a29mUT3bb492EDdn5%2BSZVR9LpjWtkEH%2FvE12o6ZTtzLiEaXk5q%2FrIWZlxoRgNEftm%2BfVTeknuybqIm7RvU9R9TyPyrFxzF3LiFu4tUPTPpby0J8KQR6NXa%2B6yb5emiEUID0rtcKy3FgyMvz3sCzZg97L3r1hygC9PZhPRh41As6bdMZpK9iPk0%2BEhx5P0GNHzwyi2rdR7uFdKuybkj0xoebAu0AUGMfjvjAvdmh8mnxdqWx2WBEbnHdjwn%2FhwnP2Jv8fa13Ib28x8uePmIHqu70zvzssy0lJdWjFAo',
        '__EVENTVALIDATION':'DBXz0iKND4TU2%2FViF1aOsX685s8Ti4vACcuYs6wQAa5V0iQlJNaVRtf4RH09jiUP9ajpUOz2lnPf%2BavCGIC6THXzVOpmz1to0Gj4%2F4uqP6uxrZ%2BfVyVyN%2Fuc3pJOjcTo4%2Fg3dlrn0drF8mksgmm5fKmb65uyqx2x%2BYJhZCezRIDsC7naPVB8A9TlsScwDed1pswYaAIirIo4rxnCbfxwzIjkVbW1X%2FRo3zH6NwrE%2FBLmTwa4c1DjHpCDzA2e%2FdyRzsw7%2BegGrazUn1kZzLb117nfyYADfwDJpSeU0vpxCL%2FFYB%2BosgYf3Q13c4b3SZFCE4Ig%2B4aEFrcM160SLd%2FywWYPqXsUpM%2FO9ifjIrt25snp2lIB%2B%2B%2B2EUXGFo8OblhjdXOYarFnMARKuQS2o1cEV%2BSw3I68WZ%2BtjGFmmdi3iVDyQUCUJxdHW%2FBsnTtuUvlQkgsSJ2VS3EOx4b2DoT3Xk4821E7vUiJj7G%2BCTVLbq3CqBm4x9dtB%2FS5UIvOEwLG7%2BlmEs4gcdzX%2Fc7QmsiYJdUgaTXXgEmrgwdfUrAiQ%2BQoXSQiLT%2BhCgDY0DGvS5oW6J9vDKBG6w9pio%2FWEysbtOC2xsNnV4OFULsWLpJk5dXxXgbS3k3rllJa7klq0Gq%2Bu%2FVjRXwKk4IevnfnDScaW7oDCCI66UZAMPOW0uHWyXk%2FXY3Aw49gRCT%2B7I35YWGWc4Df5u%2BblqQ284ws772Z%2B5oD%2F6GWRJXumP8KZIJuicgLg2I5aeIQfD2AgGDm4RboTRQpF2WSpUpmOt9%2FwS2Z9VbNFsMp8szcgFxCTQOlbPgX%2BZzlfuQuRY2GYsxF3gNQjTHwtRnFfUspLlCHFpFqpPqay7TeGoPq0oQ7snhKXf1VuFr%2BtMBeLcZjreM9nbKgmB0lt1LkNkbcJUlaMWgfcGsRwqMvLK1WPY1AH6ZXjfaa5tWXUTY622IhWg%2BwJzHL0i%2BBAGjV9umLhGKrEsfsEH5lZBHYo7t%2BDxW47OwZj3UjOTjIVjJWUgTPmWri8UtXoDpDM%2Fzwk1PApf5hw%2Fvt81pje4mu11GQa5K0ey9EkStYggfDE8DYILiNwTNRBJ339VyuezGTB7s8TbmYPwhoA6fBsiPil4Zn3%2Fg%2BPqQA1wBdotAwUq8BSguzsd78CHLyrBZILDdG7TzNHumywvVKWgZ4T%2F1KkikVRhTGzks7Yaby95Rv6StDxm9wJw6ohSi0yZWVSa7Kj6NOIO6GjkVhiwPWaUuwH9%2FdSAKRAKhaUl180hfv7bNMVEXxakQcw3eiDi7oVNwHQmVbvfwxg3RZoTA3XCKKBgVxUFElynzNUUTPWORO55%2FLaPRFjZgjLvpEnecKWmhIhvFu0Mzu4%2FZapiguuvufo1mKC0ApcaP3v51BmRlIq9SF3O9PsGGUZaDFb5T46VeF2cDN2qFxh61Pr95GFqrkIQGiuA6oIunW%2B%2FxAfJt%2BP3Dh20LSGs9ckfAOIfi3yNm8f6a2vjZbs9KZZ4M4tD1gOI1cT%2F0T244fZFQdqwCowbiWrTYrPqL9FjGioJ28iWtfQhADbWOBrv%2BOhpdOxxHuQAlSK7A0mcuxAmrRHEu40mQ%2BUkbrc5oM08ul2v7z8HhQ1arXuNHlvvIj0t35Qv6dO0xOPA%2FG7U8kORePjTByqsGVaMPBJTlkj7At87UGSgagIavWO1%2BKUMPtQO7sYZe9bC9a8M5yzw%2B3GK67RwGdJtbjNs9v8Au3DlNFI%2B%2FpRdmLqjFKt9vQNHNYRVm%2BT1xICtwO2Amm11I00C1T7rXvkmneVovhLwl1L5hKHghMwada8ytIUach1VbMgKwsrv4TPUK7kc3fFrDrbrTkj81GrD0SBqPWyckts39XAjhCuB74SFaOVigmbcwFtIcubj0A7r0FzE%2FLEs2ys%2FtvkEcLNle9RwWf0bzccSW7pgmrP1TtnPA%2F2RYGObD9bvUC5OsGDARs7AMoW%2BmbZNfPWWwJvl5oF2nsMW1vaLxaL%2BwvPLGRFVBfl18HmVuntE%2BofOASn3s7DPX1ZtJPax%2BGmK6fRdQn1Znm%2FzL13V9JaFokvnz84uP20Jkf0C2wCmTGtjRYxMYnzJVSClVxOoylSeUiJfBQv%2B5aSPE9eib%2Fpmai9yQRxk7ecrirdZgtf6ejmdA3WnuKzvFJdWs%2FYlBmzJ4S5Q6Ye5KeGVvIvvh74%2FNJv5IYvHpBA1Cx0Ku0B6AzvCslkYkrSZe894wTGkBSUzxOT37XBl%2BsY2mw42Yyv5UjKMtDiKofmyDkVWdy3wAqUeN%2BNWjo7AVfx1yk2yysnjvXpSsVWSL3CW%2FaHMjSnRbM%2F05Te48sfWoZ0UHr594fQJbsTUf9k%2BFhZ8ylWIOyQbiIQ5OR%2FRwt98X0FNpKUkX1vyuIRgylAvvR%2BhlZStI90AsH4EONe1pCYTFSXZMuS8oz6vDvKOxUuJN2MslBOcjDwCsOBS9KpmgyoZtmE0fA8VAe9A9yXSECEE9oUh2L0smXK5DpfGKNxjS4m%2BInH9TAhVMgWT1hIJyuy4DgIYA1WqUl513l0a8YUFR6qsy6DlTeOWeBxQyowigRoB4ot81StnYDZzmKHd3m05P3RRPOJWlePH5v0nJyyLjtGlTwV8ldB0rCEUCXd1zkBXRcNelqHq9uaMU%2FuPwaH%2Fz2hS2SZhuR269tfcBAG8kupeoauHzgXuUlslTt6B%2FShFpMsCaM6MuduKprsv0G2BnW6WBVSkq5hx9PswMkvxQOQk6wZfrppING6YHrOWIMA8w1QAuEmvcCibuzKP0P4R%2Fs1twyUbAlCl7G7TLlRh5Nk12yK11FRuQmdFbWpNb64UuIY%2BZPoFqo0Paxz6hDXh%2FAv%2BBOEYhkT9B2W5fJ9rNB5qCKDFyENvlonPf%2Fr4%2FT4ZkA%2F55FB%2BadK72tVKy50NRtQvP3verDyLRTuk9SsRSDwByLcD4zy%2FMg%2FKZ1WzB4LvzI%2BVfseS67NTY6h7nL7KVGP%2FYS%2BiSoFWLpvfkRPilqYXE7QQB9GHUczO39eRHeaBn2xLjyhQCg3gnzvh4jUv%2BuBtYuIARDIv1%2FczJNIGaqXGwGeT9OI6zCCBNcS3tPh5BKvZMGXvSH4PExf0%2Fs%2Bacq2gat3ueZsTJZ0ZsINoxte8MDkrRP80N014ADL6tg73238omQISlkm6JLUN4B5P05NdwDCMwOKvk%2B5Rl83wJET4Svrvyea%2B%2FUC6P%2B0jhxPPzxhCIWPBgHSA3DXRkqtaVK0lSXdz1qgdC%2FcT3UgZpNaTFX0MVVA8gxmSY9eME5vytad9SPxkSBUx5jMTOP4YnlNNT6SX0n53rtXewCfgZv1HCGxmqg9CxM8TMRksjyI2Y%2FB4MuZ2FP4LUej0oj2aSnbSp8S0rgk9eMxSwu6z9EpEfc2UOJzncZ3agT9w4OyM2znL7bhmYufAVSypxnN%2B5gJL9aEgMeQxQIyLYRcekF%2BYcoiLtiak5k2C3qOjcG69P%2BNwccyMq6a3UlQtWtpf10Ad%2BAeDKlsP06a3%2BTTFaBi2Q%2FCTwkNJ7yQc3d2tN8MygZCPo%2Bz3GLT5A1rOpAWLuv4fJnNGuC2oiiXC1CWYmGVh9vCQyEiuN32GnqoE0WODBbM%2F8oA7q66IkkU0D5yhJ12X9%2FrMs7chksM5W1YewBnh3tNPC3spG6Wz9RcV6BAjFdEFwz3Hksj6CYsEwCEuZ6Gkn5iogE05qPRoOoj6RJD%2Bm2kZS%2F%2BcyQDXAa2H7Eo50igteGlKVpIysz28tbvZJU3%2BNOlrKl6rDmVNkP86L4kSzF%2BydzGhbwz6Dar3oYZ7OO8OUM6%2BznmR%2F9q5Q1m%2BaupgZYSvGwpL%2F4v54FjCHglwt978%2B4GZIs%2Fn5XQcurqgsb%2BckwDJZTsbF6AAfYHv%2F8CSVgC0Adr2yCNlatI3VnZ2N%2BehkNhe96POydCIGwoif8HkM2BjUf5qb8fEWVbpYqLhTo7DTuJD9wZGpu8ZCgnqhyKudH8eViY2AG87WRA%2B%2BmDBXuGmmYLDiko4nRAu3uv0Sw6PecnUmqJ2S9ah2poctsD6RwxEmxQthngRvhtQcFJu11kXVCiMTs4aAenKd73RknG6dj3tRJQ%2FNkwjAF0%2BVpGPTPkyqQX9wGjDTFqc55QFg%2B7fqGQErMoj3EwKYtFTzj%2BHDvqHjO2upVpge5nX82bpWAgAPwwvS%2Bo8XcERxIszn9fEA2Kcuh0kfw%2BB8KWsnBENAABqPY6CMbiBd40KPcKbJktefp7TGxNzZVe%2Frk%2FPcYrxXagLN00q68m%2Br4x%2FtO%2FC977XPiOwisy8yLXikL3%2Fc4p8L1q9%2FVzsnDjFBKU%2Fo%2FGfip7XQgVMALAhmln4IdDS1shGtRJvd2Opg6yt8o6%2BBOPNhv037gmU0z1Ivny6tZSkCQrvE2RRMRvpj032KJfYPvurpiEalXNMCdO1p95M71swYNIaUJioqhrSRYjD0p3jSX8jzdlkncshkmUO8PKRxNM8i0tuaXZTLrLwOZuuminlq0fYayuJRXMWgk%2B4FwGmfQ8VAzVxMde4snFE93wro%2BFfScmC3PRwQN4UYO0vAzn9x6doBu5fRz%2FNBJg3EIUIpUyt4ntGrQ8XS8FPu2GzPFWvzgg9m6NhLGMuqBS%2BxT00OrLBPw%2FV6hJhGwnv7rBzf5sXSGraof0pjh%2F1qX790MDUtOaPxK9GgI8ZfR%2Fezq4%2BX2fu4Om8FPCI1tn6krOhmxQxwXv3MG9mmSwHPPsCYJGjaAScLRZwQIt7TZXKBMeV31pZws4FNIEuoM9bqszyNAnq9%2Fgc1jjqwu0ALa6RZ5L3ivW2tUJZMubfUdvSB0GRlOei7bDCY%2Fv1F0prgGQh93%2FYcMcIfqx%2FX2lu5H2NC9cMXBkCoOtQdY2LcYhZUStwlS5%2F7hUOfUqAhCKsrVILY6U3QmodwZmFDbZt2at7NuxpRhsDb0AiaYByTvXkm7%2Fajy6DzQpyYjrkFpa0rC5uEgYc3znBcqRu%2BD25g%3D%3D',
    }.items())
    return requests.post(url, headers=headers, data=data)

def _extract_results(html, year, season):
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
    if args.time:
        filters.append((lambda offering: any((meeting.start_time < datetime.strptime(args.time.upper(), '%I:%M%p') < meeting.end_time) for meeting in offering.meetings if meeting.start_time)))
    if args.day:
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
