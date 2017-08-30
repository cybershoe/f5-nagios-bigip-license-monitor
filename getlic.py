#!/usr/bin/env python

DEFAULT_CRIT_THRESHOLD = 3
DEFAULT_WARN_THRESHOLD = 7

import argparse
import string
import sys

from urllib3 import disable_warnings
from f5.bigip import ManagementRoot

def scrub(args):
    printable = set(string.printable)
    for a in [x for x in args if isinstance(args[x], str)]:
        for c in args[a]:
            if not c in printable:
                sys.stderr.write('Unprintable character in ' + a)
                sys.exit(3)

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

if args['insecure']:
    disable_warnings()

try:
    mgmt = ManagementRoot(args['hostname'], args['username'], args['password'], token=args['loginref'])
except Exception as e:
    sys.stderr.write('Unable to connect to ' + args['hostname'] + '\n')
    if args['verbose']:
        sys.stderr.write(str(e))
    sys.exit(3)

try:
    license = mgmt.tm.shared.licensing.registration.load()
except Exception as e:
    sys.stderr.write('Unable to retrieve license activation information\n')
    if args['verbose']:
        sys.stderr.write(str(e))
    sys.exit(3)

print(license.expiresInDaysMessage)

if float(license.expiresInDays) <= args['crit_threshold']:
    sys.exit(2)
elif float(license.expiresInDays) <= args['warn_threshold']:
    sys.exit(1)
