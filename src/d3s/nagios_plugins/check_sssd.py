#!/usr/bin/env python3

#
# Copyright 2026 Vojtech Horky
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
from d3s.units import SmartUnit


class CheckSSSD(NagiosPluginBase):
    """
    Checks that SSSD domain is online.

    ===

    Example output:

        SSSD OK - domain default is online|domain=default,status=online

    """

    STATUS_RE = re.compile('^Online status: (.*)$')

    def __init__(self):
        NagiosPluginBase.__init__(self, 'SSSD')
        self.add_param('domain', 'default', '--domain')

    def collect(self):
        # Read memory information
        try:
            command = ['sssctl', 'domain-status', '--online', self.domain]
            output = list(self.read_command_output(command))
            result = next(self.grep_lines(CheckSSSD.STATUS_RE, output))
        except IOError as e:
            self.worsen_to_critical()
            self.set_message(f'unable to query domain status: {e}')
            return
        except StopIteration as e:
            self.worsen_to_critical()
            if (len(output) > 0) and (output[0] == 'Unable to get online status'):
                self.set_message('unable to query domain status (probably wrong domain name)')
            else:
                self.set_message('unable to query domain status: ' + ' '.join(output))
            return
        domain_status = result.group(1).lower()
        self.add_perf_data('domain', self.domain)
        self.add_perf_data('status', domain_status)
        if domain_status != 'online':
            self.worsen_to_critical()
        self.set_message_from_perf('domain {domain} is {status}')

def main():
    """
    Module main for execution from shell script.
    """
    CheckSSSD().run(True)

if __name__ == '__main__':
    main()
