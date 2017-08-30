# f5-nagios-bigip-license-monitor
Nagios plugin to monitor time remaining on a BIG-IP evaluation license
 
## Command definition:

```
# 'check_bigip-license' command definition
define command{
        command_name    check_bigip-license
        command_line    $USER1$/check_bigip-license.py -H $HOSTADDRESS$ $ARG1$
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
usage: check_bigip-license.py [-h] -H <hostname> -u <username> -p <password
                              [-l <loginref>] [-w <warn_threshold>]
                              [-c <crit_threshold>] [-i] [-v]

Check BIG-IP License Expiry

optional arguments:
  -h, --help            show this help message and exit
  -H <hostname>, --host <hostname>
                        Mandatory. Specifies the hostname or IP to check.
  -u <username>, --username <username>
                        Mandatory. Specifies the iControl user account
                        username.
  -p <password>, --password <password>
                        Mandatory. Specifies the iControl user account
                        password.
  -l <loginref>, --loginref <loginref>
                        Optional. Overrides the iControlREST loginReference
  -w <warn_threshold>, --warn-threshold <warn_threshold>
                        Optional. Specifies the warning threshold in days.
  -c <crit_threshold>, --crit-threshold <crit_threshold>
                        Optional. Specifies the critical threshold in days.
  -i, --insecure        Optional. Suppress SSL warnings
  -v, --verbose         Optional. Verbose error messages.
```
