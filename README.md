# f5-nagios-bigip-license-monitor
Nagios plugin to monitor time remaining on a BIG-IP evaluation license
 
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
