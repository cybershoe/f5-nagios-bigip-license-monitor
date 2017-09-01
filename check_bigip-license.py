#!/usr/bin/env python

'''

Nagios plugin to monitor time remaining for time-limited BIG-IP license.

Requires at least hostname, username, and password.

Example command definition in Nagios:

# 'check_bigip-license' command definition
define command{
        command_name    check_bigip-license
        command_line    $USER1$/check_bigip-license.py -H $HOSTADDRESS$ $ARG1$
        }

Example service definition in Nagios:

# Monitor license expiry via iControl
define service{
        use                     generic-service ; Inherit values from a template
        hostgroup_name          bigip-hostgroup
        service_description     license
        check_command           check_bigip-license!-u service_account -p "password_here"
        normal_check_interval   1440
        notification_interval   1440
        retry_check_interval    60
        }

'''

DEFAULT_CRIT_THRESHOLD = 3
DEFAULT_WARN_THRESHOLD = 7

import argparse
import string
import sys

from datetime import date, datetime, timedelta
from f5.bigip import ManagementRoot
from f5.sdk_exception import LazyAttributesRequired
from pytz import timezone
from urllib3 import disable_warnings

_verr = False

def scrub(args):
    printable = set(string.printable)
    for a in [x for x in args if isinstance(args[x], str)]:
        for c in args[a]:
            if not c in printable:
                sys.stderr.write('Unprintable character in {0}\n'.format(a))
                sys.exit(3)

def parse():
    parser = argparse.ArgumentParser(description='Nagios plugin to monitor time remaining for time-limited BIG-IP licenses')

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
    global _verr
    _verr = args['verbose']

    # Scrub inputs for non-printable characters
    scrub(args)

    return args

def connectBigIP(host, user, passwd, loginref):
    try:
        mgmt = ManagementRoot(host, user, passwd, token=loginref)
        return mgmt
    except Exception as e:
        sys.stderr.write('Unable to connect to {0}\n'.format(host))
        if _verr:
            sys.stderr.write(str(e))
        sys.exit(3)

def getLicense(bigip):
    try:
        license = bigip.tm.shared.licensing.registration.load()
        return license
    except Exception as e:
        sys.stderr.write('Unable to retrieve license activation information\n')
        if _verr:
            sys.stderr.write(str(e))
        sys.exit(3)

def checkSubs(license, tz, warn, crit):
    try:
        for m in [x for x in license.moduleEvaluations]:
            code = [0]
            exDateStr = m['moduleName'].split('|')[3]
            modName = m['moduleName'].split('|')[0]
            exTime = timezone(tz).localize(datetime(int(exDateStr[0:4]), int(exDateStr[4:6]), int(exDateStr[6:8])))
            remaining = exTime + timedelta(days=1) - datetime.today().astimezone(timezone('utc')) # License expires at end of day local time
            if remaining.seconds > 0:
                print('{0} expires in {1} days, {2} hours.'.format(modName, remaining.days, remaining.seconds // 3600))
            else:
                print('{0} has expired.'.format(modName))
            if remaining.days < crit:
                code.append(2)
            elif remaining.days < warn:
                code.append(1)
        return max(code)
    except LazyAttributesRequired:
        print('No time-limited modules')
        return 0

def checkBase(license, tz, warn, crit):
    try:
        exTime = timezone(tz).localize(datetime(*map(int, license.licenseEndDateTime.split('T')[0].split('-'))))
        remaining = exTime + timedelta(days=1) - datetime.today().astimezone(timezone('utc')) # License expires at end of day local time
        if remaining.seconds > 0:
            print('Base license expires in {0} days, {1} hours.'.format(remaining.days, remaining.seconds // 3600))
        else:
            print('Base license has expired.')
        if remaining.days < crit:
            return 2
        elif remaining.days < warn:
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

devs = bigip.tm.cm.devices.get_collection()
tz = [x for x in devs if x.selfDevice == 'true'][0].timeZone
devTime = datetime.today().astimezone(timezone(tz))

license = getLicense(bigip)

subs = checkSubs(license, tz, args['warn_threshold'], args['crit_threshold'])
base = checkBase(license, tz, args['warn_threshold'], args['crit_threshold'])

sys.exit(max(subs, base, 0))
