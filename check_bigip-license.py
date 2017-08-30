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

def scrub(args):
    printable = set(string.printable)
    for a in [x for x in args if isinstance(args[x], str)]:
        for c in args[a]:
            if not c in printable:
                sys.stderr.write('Unprintable character in ' + a)
                sys.exit(3)

def parse():
    parser = argparse.ArgumentParser(description='Check BIG-IP License Expiry')

    parser.add_argument('-H', '--host',
      required=True,
      dest='hostname',
      metavar='<hostname>',
      help='Mandatory. Specifies the hostname or IP to check.')
    parser.add_argument('-u', '--username',
      required=True,
      dest='username',
      metavar='<username>',
      help='Mandatory. Specifies the iControl user account username.')
    parser.add_argument('-p', '--password',
      required=True,
      dest='password',
      metavar='<password>',
      help='Mandatory. Specifies the iControl user account password.')
    parser.add_argument('-l', '--loginref',
      dest='loginref',
      metavar='<loginref>',
      help='Optional. Overrides the iControlREST loginReference',
      default=True)
    parser.add_argument('-w', '--warn-threshold',
      dest='warn_threshold',
      metavar='<warn_threshold>',
      help='Optional. Specifies the warning threshold in days.',
      type=int,
      default=DEFAULT_WARN_THRESHOLD)
    parser.add_argument('-c', '--crit-threshold',
      dest='crit_threshold',
      metavar='<crit_threshold>',
      help='Optional. Specifies the critical threshold in days.',
      type=int,
      default=DEFAULT_CRIT_THRESHOLD)
    parser.add_argument('-i', '--insecure',
      dest='insecure',
      action='store_true',
      help='Optional. Suppress SSL warnings',
      default=False)
    parser.add_argument('-v', '--verbose',
      dest='verbose',
      action='store_true',
      help='Optional. Verbose error messages.',
      default=False)

    args = vars(parser.parse_args())

    # Scrub inputs for non-printable characters
    scrub(args)

    return args

def connectBigIP(h, u, p, l):
    try:
        mgmt = ManagementRoot(h, u, p, token=l)
        return mgmt
    except Exception as e:
        sys.stderr.write('Unable to connect to ' + h + '\n')
        if args['verbose']:
            sys.stderr.write(str(e))
        sys.exit(3)

def getLicense(bigip):
    try:
        license = bigip.tm.shared.licensing.registration.load()
        return license
    except Exception as e:
        sys.stderr.write('Unable to retrieve license activation information\n')
        if args['verbose']:
            sys.stderr.write(str(e))
        sys.exit(3)

def checkSubs(license, warn, crit):
    try:
        for m in [x for x in license.moduleEvaluations]:
            code = [0]
            exDateStr = m['moduleName'].split('|')[3]
            modName = m['moduleName'].split('|')[0]
            exDate = datetime(int(exDateStr[0:4]), int(exDateStr[4:6]), int(exDateStr[6:8]))
            remaining = exDate - datetime.today()
            print('{0} expires in {1} days, {2} hours.'.format(modName, remaining.days + 1, remaining.seconds // 3600))
            if remaining.days + 1 < crit:
                code.append(2)
            elif remaining.days + 1 < warn:
                code.append(1)
        return max(code)
    except LazyAttributesRequired:
        print('No time-limited modules')
        return 0

def checkBase(license, warn, crit):
    try:
        print(license.expiresInDaysMessage)
        if float(license.expiresInDays) <= args['crit_threshold']:
            return 2
        elif float(license.expiresInDays) <= args['warn_threshold']:
            return 1
        else:
            return 0
    except LazyAttributesRequired:
        print('Base license is perpetual')
        return 0

args = parse()

if args['insecure']:
    disable_warnings()

bigip = connectBigIP(args['hostname'], args['username'], args['password'], args['loginref'])

license = getLicense(bigip)

subs = checkSubs(license, args['warn_threshold'], args['crit_threshold'])
base = checkBase(license, args['warn_threshold'], args['crit_threshold'])

sys.exit(max(subs, base))
