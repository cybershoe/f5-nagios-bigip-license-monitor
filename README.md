# f5-nagios-bigip-license-monitor
Nagios plugin to monitor time remaining on a BIG-IP evaluation license

After forgetting yet again to re-license my lab before the license expired, I decided to bite the bullet and get Nagios set up so that I could poll the license expiry time via SNMP. Then, I found out that we don't have an OID for the LicenseEndDate attribute. Fun times.
 
So, instead I hacked together this this plugin as a bash script to pull the end date using cURL and jq, and alert accordingly. By default it changes the service state to WARNING when the license is 7 days away from expiry, and CRITICAL at 3 days. Put the .sh file in your Nagios plugins folder (/usr/local/nagios/libexec by default), and configure command and service definitions similar to the following:
 
## Command definition:

```
# 'check_bigip-license' command definition
define command{
        command_name    check_bigip-license
        command_line    $USER1$/check_bigip-license.sh -H $HOSTADDRESS$ $ARG1$
        }
```

## Service definition:
```
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
``` 
 
## Script usage:
```
Usage:
 
check_bigip-license.sh <options>
 
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
```
