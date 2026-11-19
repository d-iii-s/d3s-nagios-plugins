# D3S Nagios Plugins

A collection of various mini-plugins for Nagios.



## Installation (inside virtualenv)

```shell
python -m venv env
. ./env/bin/activate
pip install -e .
# Now it is possible to run any of the ./env/bin/nagios_d3s_check_* scripts
```



## Available plugins


### `check_health`

Only collects basic system status (uptime, free memory, ...), useful only
for performance data analysis.


### `check_memory`

Checks available memory.


### `check_os_updates`

Checks that GNU/Linux system is up-to-date.


### `check_sssd`

Checks that SSSD domain is online.


### `check_systemd_service`

Checks that systemd unit is enabled and running.



## Utilities

Besides the plugins, the package installs the following helper tools. These
are not Nagios plugins and are not meant to be run by Nagios.


### `nagios_d3s_status_dat_to_json`

Converts the Nagios `status.dat` file to JSON which is easier to parse by
other tools (e.g. a Jinja template and similar).

For each host and service it reports the state, time in that state, flags
(acknowledged, soft state, downtime, flapping), the plugin output, the long
plugin output and the performance data (both parsed and raw).

```shell
nagios_d3s_status_dat_to_json [--sort | --worst-first] [/var/spool/nagios/status.dat]
```

By default, hosts and services keep the order from `status.dat`. Use `--sort`
to sort them alphabetically or `--worst-first` to list the worst problems
first.

The produced JSON is stable (sorted keys).

