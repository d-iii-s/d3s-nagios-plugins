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
Checks avaiable updates.

Usage:
    <no parameters needed>

Example output:



"""

import re
import urllib.request
from d3s.nagios import NagiosPluginBase


class CheckOsUpdates(NagiosPluginBase):
    """
    Checks available updates and warns when too many packages are outdated.
    """

    OS_RELEASE_RE = re.compile('^([a-z_A-Z]+)=["]?([^"]*)["]?$')

    FEDORA_LIST_UPDATES_CMD = [
        'dnf',
        'list',
        '--quiet',
        'updates'
    ]

    FEDORA_RELEASE_LIST_URL = 'https://download.fedoraproject.org/pub/fedora/linux/releases/'

    FEDORA_RELEASE_RE = re.compile('''
        a\\s+
        href=['"]([0-9]+)/?['"][ \t>]
        ''', re.VERBOSE)

    def __init__(self):
        NagiosPluginBase.__init__(self, 'OS-UPDATES')
        self.warn_on = 50
        self.critical_on = 200

    # pylint: disable=no-self-use
    def get_fedora_latest_(self):
        """ Get latest Fedora release as integer. """
        response = urllib.request.urlopen(CheckOsUpdates.FEDORA_RELEASE_LIST_URL)
        text = response.read().decode('utf-8')
        releases = re.findall(CheckOsUpdates.FEDORA_RELEASE_RE, text)
        return max([int(r) for r in releases])

    def collect_fedora_(self):
        """ Collect information for Fedora distribution. """
        self.add_perf_data('os_latest_version', self.get_fedora_latest_())
        if self.get_perf_data('os_version') + 1 < self.get_perf_data('os_latest_version'):
            self.worsen_to_critical()
            message_suffix = ' too old ({os_latest_version} available)'
        else:
            message_suffix = ''

        outdated_list = self.read_command_output(CheckOsUpdates.FEDORA_LIST_UPDATES_CMD)
        outdated = sum(1 for _ in outdated_list)
        # Strip header
        if outdated > 1:
            outdated = outdated - 1
        self.add_perf_data('os_outdated_packages', outdated)

        if outdated > self.warn_on:
            self.worsen_to_warning()
        if outdated > self.critical_on:
            self.worsen_to_critical()

        self.set_message_from_perf('Fedora {os_version}' + message_suffix
                                   + ', {os_outdated_packages} out-dated packages')


    def collect(self):
        self.add_perf_data('os_id', 'unknown')
        try:
            release_file = self.read_file('/etc/os-release')
            for entry in self.grep_lines(CheckOsUpdates.OS_RELEASE_RE, release_file):
                key = entry.group(1)
                value = entry.group(2)
                if key == 'ID':
                    self.add_perf_data('os_id', value)
                elif key == 'VERSION_ID':
                    self.add_perf_data('os_version', int(value))
        except IOError:
            pass

        kernel_release = next(self.read_command_output(['uname', '-r']))
        self.add_perf_data('os_kernel', kernel_release)

        os_id = self.get_perf_data('os_id')
        if os_id == 'unknown':
            self.worsen_to_critical()
            self.set_message('unknown OS')
        elif os_id == 'fedora':
            self.collect_fedora_()
        else:
            self.worsen_to_critical()
            self.set_message_from_perf('unsupported OS {os_id}')


def main():
    """
    Module main for execution from shell script.
    """
    CheckOsUpdates().run(True)

if __name__ == '__main__':
    main()
