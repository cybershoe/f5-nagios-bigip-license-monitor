#!/bin/bash

###############################################################################
#
# check_bigip-license.sh
#
# (C) 2016 F5 Networks Canada, Ltd.
#
# Author: Adam Schumacher <a,schumacher@f5.com>
#
###############################################################################
#
# This is a Nagios plugin to alert when the license on a BIG-IP system is
# close to expiry.
#
# Dependencies:
#
# cURL - To query iControlREST API
# jq - To parse JSON responses
#
# Usage:
# 
# check_bigip-license.sh <options>
#
# Options:
#
# -H <host> 
# Mandatory. Specifies the hostname or IP address to check.
#
# -u <usermame>
# Mandatory. Specifies the iControl user account username.
#
# -p <password>
# Mandatory. Specifies the iControl user account password.
#
# -w <warn_threshold>
# Optional. Specifies the warning threshold in days. If not specified, the
# value of DEFAULT_WARN_THRESHOLD is used instead.
#
# -c <crit_threshold>
# Optional. Specifies the critical threshold in days. If not specified, the
# value of DEFAULT_CRIT_THRESHOLD is used instead.
#
# Notes:
#
# This has only been tested against time-limited evaluation licenses. I have
# included logic to detect when being run against a perpetual license, but
# this has not been tested.
#
###############################################################################


DEFAULT_WARN_THRESHOLD=7
DEFAULT_CRIT_THRESHOLD=3

# Parse command line options

while getopts :H:u:p:w:c: opt; do
  case $opt in
    H)
      HOST=$OPTARG
      ;;
    u)
      USERNAME=$OPTARG
      ;;
    p)
      PASSWORD=$OPTARG
      ;;
    w)
      WARN_THRESHOLD=$OPTARG
      ;;
    c)
      CRIT_THRESHOLD=$OPTARG
      ;;
    \?)
      >&2 echo "Invalid option: -$OPTARG"
      exit 3
      ;;
    :)
      >&2 echo "Option -$OPTARG requires an argument"
      BADVARS=1
      ;;
  esac
done

# Validate inputs

if [ -z "$HOST" ]
then
  >&2 echo "Host required (-H option)"
  BADVARS=1
fi

if [ -z "$USERNAME" ]
then
  >&2 echo "Username required (-u option)"
  BADVARS=1
fi

if [ -z "$PASSWORD" ]
then
  >&2 echo "Password required (-p option)"
  BADVARS=1
fi
if [ -z "$WARN_THRESHOLD" ]
then
  WARN_THRESHOLD=$DEFAULT_WARN_THRESHOLD
elif [[ ! "$WARN_THRESHOLD" =~ ^-?[0-9]+$ ]]
then
  >&2 echo "Warning threshold must be an integer"
  BADVARS=1
fi

if [ -z "$CRIT_THRESHOLD" ]
then
  CRIT_THRESHOLD=$DEFAULT_CRIT_THRESHOLD
elif [[ ! "$CRIT_THRESHOLD" =~ ^-?[0-9]+$ ]]
then
  >&2 echo "Critical threshold must be an integer"
  BADVARS=1
fi

if [ ! -z "$BADVARS" ]
then
  cat <<EOF

Usage:

$(basename "$0") <options>

Options:

-H <host> 
Mandatory. Specifies the hostname or IP address to check.

-u <usermame>
Mandatory. Specifies the iControl user account username.

-p <password>
Mandatory. Specifies the iControl user account password.

-w <warn_threshold>
Optional. Specifies the warning threshold in days. If not specified, the
value of DEFAULT_WARN_THRESHOLD is used instead.

-c <crit_threshold>
Optional. Specifies the critical threshold in days. If not specified, the
value of DEFAULT_CRIT_THRESHOLD is used instead.
EOF
  exit 3
fi

# Retrieve authentication token

TOKEN=$(curl -sk https://$HOST/mgmt/shared/authn/login -H "Accept: application/json" -H "Content-Type: application/json" -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\",\"loginProviderName\":\"tmos\"}" | jq -r .token.token)

if [ $? -ne 0 ]
then
  (>&2 echo "Unable to retrieve authentication token")
  exit 3
elif [ -z $TOKEN ]
then
  (>&2 echo "Invalid token received")
  exit 3
fi

# Retrieve license end date

EXPIRY=$(curl -sk https://$HOST/mgmt/tm/sys/license/ -H "Accept: application/json" -H "Content-Type: application/json" -H "X-F5-Auth-Token: $TOKEN" | jq -r '.entries[].nestedStats.entries.licenseEndDate.description')

if [ $? -ne 0 ]
then
  >&2 echo "Unable to retrieve expiry date"
  exit 3
fi

# REVIEW: If null, assume perpetual license

if [ "$EXPIRY" == "null" ]
then
  echo "Perpetual License"
  exit 0
else # Otherwise find number of days until expiration
  (( REMAIN = (( $(date -d $EXPIRY +%s) - $(date +%s) )) / 86400 ))
fi

echo "License: $REMAIN days remaining"

if [ "$REMAIN" -le "$CRIT_THRESHOLD" ]
then
  exit 2
elif [ "$REMAIN" -le "$WARN_THRESHOLD" ]
then
  exit 1
fi
