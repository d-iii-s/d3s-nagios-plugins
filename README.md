# D3S Nagios Plugins

A collection of various mini-plugins for Nagios.



## Installation (inside virtualenv)

```shell
virtualenv env
. ./env/bin/activate
./setup.py install
# Now it is possible to run any of the ./env/bin/nagios_d3s_check_* scripts
```



## Available plugins


### `check_health`

Only collects basic system status (uptime, free memory, ...), useful only
for performance data analysis.


### `check_memory`

Checks available memory.


### `check_systemd_service`

Checks that systemd unit is enabled and running.
