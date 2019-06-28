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
Checks available memory.

Usage:
    <no parameters needed>

Example output:
    MEM OK - 16G, 9G available (57%)|\
        mem_total_kb=16300840K,mem_avail_kb=9298876K,mem_avail_percent=57.\
        top_1_app=java:1681144:10.3:00_31_06:last-argument,\
        top_2_app=...\
        ...

"""

import re
from d3s.nagios import NagiosPluginBase
from d3s.units import SmartUnit


class CheckMemory(NagiosPluginBase):
    """
    Checks available memory and warns if there is not enough memory.

    Also reports top memory-eaters.
    """

    MEM_INFO_RE = re.compile('^([^:]*):[ \t]*([0-9]*) kB$')
    TOP_EATERS_CMD = [
        'ps',
        '-e', '--no-header',
        '--sort=-%mem',
        '-o', 'rss,%mem,comm,time,command'
    ]
    TOP_EATERS_RE = re.compile('''
        ^([0-9]+)\\s+
        ([0-9.]+)\\s+
        ([^ \t]+)\\s+
        ([0-9][0-9]:[0-9][0-9]:[0-9][0-9])\\s+
        .*?([^ \t]+)$
        ''', re.VERBOSE)

    def __init__(self):
        NagiosPluginBase.__init__(self, 'MEM')
        self.top_eaters_count = 5
        self.warn_on = 0.1
        self.critical_on = 0.05

    def collect(self):
        # Read memory information
        for entry in self.grep_lines(CheckMemory.MEM_INFO_RE, self.read_file('/proc/meminfo')):
            key = entry.group(1)
            value = entry.group(2)
            if key == 'MemTotal':
                self.add_perf_data('mem_total_kb', SmartUnit(int(value), 'K'))
            elif key == 'MemAvailable':
                self.add_perf_data('mem_avail_kb', SmartUnit(int(value), 'K'))

        avail_amount = self.get_perf_data('mem_avail_kb') / self.get_perf_data('mem_total_kb')
        self.add_perf_data('mem_avail_percent', avail_amount * 100)

        if avail_amount < self.warn_on:
            self.worsen_to_warning()

        if avail_amount < self.critical_on:
            self.worsen_to_critical()

        # Find top memory-eaters.
        top_output = self.read_command_output(CheckMemory.TOP_EATERS_CMD)
        index = 1
        for line in self.grep_lines(CheckMemory.TOP_EATERS_RE, top_output):
            value = '{command}:{rss}:{mem}:{time}:{arg}'.format(
                rss=line.group(1),
                mem=line.group(2),
                command=line.group(3).replace(':', '_'),
                time=line.group(4).replace(':', '_'),
                arg=line.group(5).replace(':', '_')
            )
            key = 'top_{}_app'.format(index)
            self.add_perf_data(key, value)
            index = index + 1
            if index > self.top_eaters_count:
                break

        # Format final message
        self.set_message_from_perf("{mem_total_kb:smart}, {mem_avail_kb:smart} available"
                                   + " ({mem_avail_percent:.0f}%)")

def main():
    """
    Module main for execution from shell script.
    """
    CheckMemory().run(True)

if __name__ == '__main__':
    main()
