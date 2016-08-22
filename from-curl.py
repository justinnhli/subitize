#!/usr/bin/env python3

import re

with open('curl') as fd:
    data = dict(arg.split('=', maxsplit=1) for arg in re.search("--data '([^']*)'", fd.read()).group(1).split('&'))
assert data
with open('eventvalidation.data', 'w') as fd:
    fd.write(data['__EVENTVALIDATION'])
with open('viewstate.data', 'w') as fd:
    fd.write(data['__VIEWSTATE'])
