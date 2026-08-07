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

import re
from d3s.nagios import NagiosPluginBase


class CheckOsUpdates(NagiosPluginBase):
    """
    Checks available updates and warns when too many packages are outdated.
    """

    OS_RELEASE_RE = re.compile('^([a-z_A-Z]+)=["]?([^"]*)["]?$')

    DNF_LIST_UPDATES_CMD = [
        'dnf',
        'list',
        '--quiet',
        '--upgrades',
    ]

    def __init__(self):
        NagiosPluginBase.__init__(self, 'OS-UPDATES')
        self.warn_on = 50
        self.critical_on = 200

    def update_eol_(self, product_id):
        eol_info = self.get_endoflife_info(
            product_id,
            self.get_perf_data('os_version')
        )
        self.add_perf_data('os_latest_version', eol_info['latest'])
        self.add_perf_data('os_is_maintained', eol_info['is_maintained'])

    def get_release_info_message_(self):
        res = ''
        if not self.get_perf_data('os_is_maintained'):
            res = ' is past its EOL'
        latest = self.get_perf_data('os_latest_version')
        if self.get_perf_data('os_version') == latest:
            # res = f'{res} (latest)'
            pass
        else:
            res = f'{res} ({latest} available)'
        return res

    def set_state_from_eol_(self):
        if self.get_perf_data('os_version') != self.get_perf_data('os_latest_version'):
            self.worsen_to_warning()
        if not self.get_perf_data('os_is_maintained'):
            self.worsen_to_critical()


    def collect_dnf_based_(self, distribution_name):
        outdated_list = list(
            self.non_empty_lines(
                self.read_command_output(CheckOsUpdates.DNF_LIST_UPDATES_CMD)
            )
        )
        outdated = len(outdated_list)
        # Strip header
        if outdated > 1:
            outdated = outdated - 1
        self.add_perf_data('os_outdated_packages', outdated)

        if outdated > self.warn_on:
            self.worsen_to_warning()
        if outdated > self.critical_on:
            self.worsen_to_critical()

        message_suffix = self.get_release_info_message_()
        message_main = distribution_name + ' {os_version}' + message_suffix + ', '
        message_details = '{os_outdated_packages} out-dated packages'
        self.set_message_from_perf(message_main + message_details)

    def collect_centos_(self):
        """ Collect information for CentOS distribution. """
        if self.distribution_name == 'CentOS Stream':
            self.update_eol_('centos-stream')
        else:
            self.update_eol_('centos')
        self.collect_dnf_based_('CentOS')

    def collect_fedora_(self):
        """ Collect information for Fedora distribution. """
        self.update_eol_('fedora')
        self.collect_dnf_based_('Fedora')

    def determine_os_release_(self):
        self.distribution_name = ''
        self.add_perf_data('os_id', 'unknown')
        try:
            release_file = self.read_file('/etc/os-release')
            for entry in self.grep_lines(CheckOsUpdates.OS_RELEASE_RE, release_file):
                key = entry.group(1)
                value = entry.group(2)
                if key == 'ID':
                    self.add_perf_data('os_id', value)
                elif key == 'VERSION_ID':
                    self.add_perf_data('os_version', value)
                elif key == 'NAME':
                    self.distribution_name = value
        except IOError:
            pass

    def collect(self):
        self.determine_os_release_()

        kernel_release = next(self.read_command_output(['uname', '-r']))
        self.add_perf_data('os_kernel', kernel_release)

        os_id = self.get_perf_data('os_id')
        if os_id == 'unknown':
            self.worsen_to_critical()
            self.set_message('unknown OS')
        elif os_id == 'fedora':
            self.collect_fedora_()
        elif os_id == 'centos':
            self.collect_centos_()
        else:
            self.worsen_to_critical()
            self.set_message_from_perf('unsupported OS {os_id}')

        self.set_state_from_eol_()


def main():
    """
    Module main for execution from shell script.
    """
    CheckOsUpdates().run(True)

if __name__ == '__main__':
    main()
