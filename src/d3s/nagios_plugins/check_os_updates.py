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
        'env',
        'LC_ALL=C',
        'dnf',
        'updateinfo',
        'list',
        '--quiet',
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
        return res

    def get_summary_message_parts_(self, distribution_name):
        yield f'{distribution_name} {{os_version}}'

        if not self.get_perf_data('os_is_maintained'):
            yield ' is past its EOL'

        latest = self.get_perf_data('os_latest_version')
        if self.get_perf_data('os_version') != latest:
            yield f' ({latest} available)'

        yield ','

        if self.get_perf_data('os_security_updates') > 0:
            yield ' {os_security_updates} security updates,'

        yield ' {os_outdated_packages} out-dated packages'

    def finalize_outcome_(self, distribution_name):
        msg = ''.join(self.get_summary_message_parts_(distribution_name))
        self.set_message_from_perf(msg)

        outdated = self.get_perf_data('os_outdated_packages')
        if outdated > self.warn_on:
            self.worsen_to_warning()
        if outdated > self.critical_on:
            self.worsen_to_critical()

        if self.get_perf_data('os_version') != self.get_perf_data('os_latest_version'):
            self.worsen_to_warning()
        if not self.get_perf_data('os_is_maintained'):
            self.worsen_to_critical()

    def dnf_process_outdated_list_(self, outdated):
        def parse_by_column_(col):
            if len(col) < 2:
                return (None, None, None)
            elif len(col) == 3:
                return (col[0], col[2], col[1])
            elif len(col) == 5:
                return (col[0], col[3], col[1])
            else:
                # Let us hope type is always second column
                return (col[0], 'unknown', col[1])

        for idx, line in enumerate(outdated):
            # Header
            if (idx == 0) and line.startswith('Name '):
                continue
            (update_id, update_pkg, update_type) = parse_by_column_(line.split())
            if not update_id:
                continue
            if update_type.endswith('/Sec.'):
                update_type = 'security'
            yield {
                'bug_id': update_id,
                'package': update_pkg,
                'type': update_type,
            }


    def collect_dnf_based_(self, distribution_name):
        outdated_list = list(
            self.dnf_process_outdated_list_(
                self.read_command_output(CheckOsUpdates.DNF_LIST_UPDATES_CMD)
            )
        )
        outdated = len(outdated_list)
        self.add_perf_data('os_outdated_packages', outdated)
        security_updates = len([i for i in outdated_list if i['type'] == 'security'])
        self.add_perf_data('os_security_updates', security_updates)

        self.finalize_outcome_(distribution_name)


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


def main():
    """
    Module main for execution from shell script.
    """
    CheckOsUpdates().run(True)

if __name__ == '__main__':
    main()
