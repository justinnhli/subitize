#!/usr/bin/env python3

import re
import sys
from os.path import join as join_path
sys.path.insert(1, join_path(sys.path[0], '..'))

from models import create_session, get_or_create

print(create_session)
