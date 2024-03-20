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
Nagios-releated utilities.
"""

import subprocess
import sys


class NagiosPluginBase:
    """
    Base class for Nagios plugins.

    Note that this class offers a lot of functionality that could be
    better implemented in standalone modules. But packing it all into
    one class make the implementation of individual plugins much faster.
    """

    STATUS_NAMES = ['OK', 'WARNING', 'CRITICAL', 'UNKNOWN']

    def __init__(self, name):
        self.name_ = name
        self.status_ = 0
        self.message_ = "empty message"
        self.perf_data_ = {}

    def collect(self):
        """ Called from run() to actually ollect monitored information. """
        raise NotImplementedError("Re-implement in subclass!")

    def add_perf_data(self, name, value):
        """ Add performance data. """
        self.perf_data_[name] = value

    def get_perf_data(self, name):
        """ Get performance data. """
        return self.perf_data_[name]

    def set_message(self, msg):
        """ Set the main plugin message. """
        self.message_ = msg

    def set_message_from_perf(self, msg):
        """ Set the main plugin message with {placeholders} from perf data. """
        self.set_message(msg.format(**self.perf_data_))

    def worsen_to_warning(self):
        """ Final plugin status would be warning or worse. """
        if self.status_ == 0:
            self.status_ = 1

    def worsen_to_critical(self):
        """ Final plugin status would be critical. """
        if (self.status_ == 0) or (self.status_ == 1):
            self.status_ = 2

    # pylint: disable=no-self-use
    def read_file(self, filename):
        """ Read given file and return list of its lines (rstripped). """
        with open(filename, "r") as inp:
            for line in inp:
                yield line.rstrip()

    # pylint: disable=no-self-use
    def read_command_output(self, cmd):
        """ Run given command and return list of lines on stdout (rstripped). """
        with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
            for line in proc.stdout:
                yield line.decode('utf-8').rstrip()
            proc.wait()

    # pylint: disable=no-self-use
    def grep_lines(self, regexp, lines):
        """ Return lines matching regular expression. """
        for line in lines:
            res = regexp.search(line)
            if res is not None:
                yield res

    def contains_line(self, regexp, lines):
        """ Returns whether some line matches regular expression. """
        try:
            next(self.grep_lines(regexp, lines))
            return True
        except StopIteration:
            return False

    def run(self, terminate=False):
        """ Main of the plugin that does the work. """
        self.collect()
        status_name = NagiosPluginBase.STATUS_NAMES[self.status_]
        print("{name} {status} - {message}{perf}".format(
            name=self.name_,
            status=status_name,
            message=self.message_,
            perf=self.format_perf_data_()))
        if terminate:
            sys.exit(self.status_)

    def format_perf_data_(self):
        """ Formats performance data as CSV. """
        if not self.perf_data_:
            return ""
        res = []
        for key, value in self.perf_data_.items():
            res.append("{}={}".format(key, value))
        return "|{}".format(",".join(res))
