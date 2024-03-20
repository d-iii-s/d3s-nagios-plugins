#!/usr/bin/env python3

#
# Copyright 2019 Vojtech Horky
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
Checks that systemd unit is enabled and running.

Usage:
  --service UNIT

Example output:

    SRV OK - httpd running, 12.6M, 6 tasks|\
        service_name=httpd,service_tasks=6,service_memory=12.6M

"""

import re
import argparse
from d3s.nagios import NagiosPluginBase


class CheckSystemdService(NagiosPluginBase):
    """
    Checks that given service is running and enabled.
    """

    DETAILS_BASE_RE = re.compile('''
        ^\\s+(Tasks|Memory):
        \\s+
        ([^ \t]+)
        .*$
        ''', re.VERBOSE)

    def __init__(self):
        NagiosPluginBase.__init__(self, 'SRV')
        parser = argparse.ArgumentParser()
        parser.add_argument('--service', dest='service', metavar='UNIT', required=True)
        args = parser.parse_args()
        self.service = args.service

    def collect(self):
        self.add_perf_data('service_name', self.service)

        is_enabled_output = self.read_command_output(['systemctl', 'is-enabled', self.service])
        is_enabled = self.contains_line(re.compile('^enabled$'), is_enabled_output)
        if not is_enabled:
            self.worsen_to_warning()

        is_active_output = self.read_command_output(['systemctl', 'is-active', self.service])
        is_active = self.contains_line(re.compile('^active$'), is_active_output)
        if not is_active:
            self.worsen_to_critical()

        status_output = self.read_command_output(['systemctl', 'status', self.service])
        for line in self.grep_lines(CheckSystemdService.DETAILS_BASE_RE, status_output):
            key = line.group(1)
            if key == 'Tasks':
                self.add_perf_data('service_tasks', line.group(2))
            elif key == 'Memory':
                self.add_perf_data('service_memory', line.group(2))

        details = ', {service_memory}, {service_tasks} tasks'
        if not is_active:
            self.set_message_from_perf('{service_name} not running')
        elif not is_enabled:
            self.set_message_from_perf('{service_name} running but not enabled' + details)
        else:
            self.set_message_from_perf('{service_name} running' + details)


def main():
    """
    Module main for execution from shell script.
    """
    CheckSystemdService().run(True)

if __name__ == '__main__':
    main()
