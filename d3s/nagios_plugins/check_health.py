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
Checks basic system health, useful for collecting basic stats.

Usage:
  <no parameters needed>

Example output:

    HEALTH OK - up 1 day, 0.79 load, 1 ready tasks|\
        mem_total_kb=16300840,mem_avail_kb=9947436,\
        load_1min=0.39,load_5min=0.79,load_15min=0.86,\
        tasks_runnable=1,tasks_total=952,\
        uptime=1 day

"""

import re
from d3s.nagios import NagiosPluginBase


class CheckHealth(NagiosPluginBase):
    """
    Collects basic information about running Linux system.

    There are not critical/warning limits as its main purpose is to collect
    basic system information for later processing via perf data section.
    """

    MEM_INFO_RE = re.compile('^([^:]*):[ \t]*([0-9]*) kB$')
    LOAD_AVG_RE = re.compile('''
        ^([0-9.]+) # 1 min
        \\s+
        ([0-9.]+) # 5 min
        \\s+
        ([0-9.]+) # 15 min
        \\s+
        ([0-9]+)/([0-9]+) # runnable/total tasks in the system
        \\s+.*$ # ignore rest of line
        ''', re.VERBOSE)
    UPTIME_RE = re.compile('^.*up[ \t]+([^,]*),.*$')

    def __init__(self):
        NagiosPluginBase.__init__(self, 'HEALTH')

    def collect(self):
        # Read memory information
        for entry in self.grep_lines(CheckHealth.MEM_INFO_RE, self.read_file('/proc/meminfo')):
            key = entry.group(1)
            value = entry.group(2)
            if key == 'MemTotal':
                self.add_perf_data('mem_total_kb', value)
            elif key == 'MemAvailable':
                self.add_perf_data('mem_avail_kb', value)

        # Get load average
        entry = next(self.grep_lines(CheckHealth.LOAD_AVG_RE, self.read_file('/proc/loadavg')))
        self.add_perf_data('load_1min', entry.group(1))
        self.add_perf_data('load_5min', entry.group(2))
        self.add_perf_data('load_15min', entry.group(3))
        self.add_perf_data('tasks_runnable', entry.group(4))
        self.add_perf_data('tasks_total', entry.group(5))

        # Read uptime information
        entry = next(self.grep_lines(CheckHealth.UPTIME_RE, self.read_command_output(['uptime'])))
        self.add_perf_data('uptime', entry.group(1))

        # Format final message
        self.set_message_from_perf("up {uptime}, {load_5min} load, {tasks_runnable} ready tasks")

def main():
    """
    Module main for execution from shell script.
    """
    CheckHealth().run(True)

if __name__ == '__main__':
    main()
