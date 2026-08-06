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
Unit conversion utilities.
"""

import re

class SmartUnit:
    KNOWN_SUFFIXES = {
        'K': 1024,
        'k': 1000,
        'M': 1024 * 1024,
        'G': 1024 * 1024 * 1024,
        'T': 1024 * 1024 * 1024 * 1024,
    }
    """
    Holds arbitrary value but formats it as a reasonable unit.
    """

    def __init__(self, value, size, unit=''):
        try:
            self.value = float(value)
        except ValueError:
            self.value = float('nan')
        self.size = size
        self.unit = unit

    @staticmethod
    def from_string(value):
        """
        Create SmartUnit from string that may contain also unit information.
        So from a value of 64B create SmartUnit(64, 'B') and from 4MiB create
        SmartUnit(4*1024*1024, 'B').
        """
        parts = re.match(r'(?P<number>\d+)(?P<sizeprefix>([KMGTkmgt][i]?)?)(?P<unit>[B]?)', value)
        if not parts:
            raise ValueError("This {} does not look like a unit.".format(value))
        number = int(parts.group('number'))
        sizeprefix = parts.group('sizeprefix')
        unit = parts.group('unit')
        return SmartUnit(number, sizeprefix, unit)

    def get_default_unit(self):
        return self.size + self.unit

    def get_base_value_(self):
        value = self.value
        if self.size in SmartUnit.KNOWN_SUFFIXES.keys():
            value = value * SmartUnit.KNOWN_SUFFIXES[self.size]
        return value

    def get_reasonable_value_with_unit_(self):
        """ Does the actual conversion to a reasonable unit. """
        value = self.get_base_value_()
        unit = ""
        if value > 4096:
            value = value / 1024
            unit = "K"
            if value > 4096:
                value = value / 1024
                unit = "M"
                if value > 4096:
                    value = value / 1024
                    unit = "G"

        return (value, unit)

    def __format__(self, format_name):
        value = self.value
        size = self.size
        unit = self.unit
        fmt = '{value:.0f}{size}{unit}'
        if format_name == 'smart':
            (value, size) = self.get_reasonable_value_with_unit_()
            format_name = ':.0f'
        elif format_name == 'base':
            value = self.get_base_value_()
            size = ''
        elif format_name == 'nounit':
            unit = ''
        elif format_name == '':
            pass
        elif format_name in SmartUnit.KNOWN_SUFFIXES.keys():
            value = self.get_base_value_() / SmartUnit.KNOWN_SUFFIXES[format_name]

        return fmt.format(value=value, size=size, unit=unit)

    def __sub__(self, other):
        if isinstance(other, SmartUnit):
            return SmartUnit(self.get_base_value_() - other.get_base_value_(), '', self.unit)
        elif isinstance(other, int) or isinstance(other, float):
            return SmartUnit(self.get_base_value_() - other, '', self.unit)
        return NotImplemented


    def __rtruediv__(self, other):
        return float(self) / float(other)

    def __truediv__(self, other):
        return float(self) / float(other)

    def __float__(self):
        return self.get_base_value_()

