#!/usr/bin/env python

DEFAULT_CRIT_THRESHOLD = 3
DEFAULT_WARN_THRESHOLD = 7

import argparse
import string
import sys

from datetime import date, datetime
from f5.bigip import ManagementRoot
from f5.sdk_exception import LazyAttributesRequired
from urllib3 import disable_warnings

import modules

args = parse()

if args['insecure']:
    disable_warnings()

bigip = connectBigIP(args['hostname'], args['username'], args['password'], args['loginref'])

license = getLicense(bigip)

subs = checkSubs(license, args['warn_threshold'], args['crit_threshold'])
base = checkBase(license, args['warn_threshold'], args['crit_threshold'])

sys.exit(max(subs, base))
