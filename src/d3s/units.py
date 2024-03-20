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


class SmartUnit:
    """
    Holds arbitrary value but formats it in a reasonable unit.
    """

    def __init__(self, value, size, unit=''):
        self.value = value
        self.size = size
        self.unit = unit

    def get_reasonable_value_with_unit_(self):
        """ Does the actual conversion to a reasonable unit. """
        units_1024 = ['K', 'M', 'G', 'T']
        value = self.value
        if self.size in units_1024:
            value = value * (1024 ^ (units_1024.index(self.size) + 1))
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
        if format_name == 'smart':
            (value, size) = self.get_reasonable_value_with_unit_()
            format_name = ':.0f'

        fmt = '{' + format_name + '}{}{}'
        return fmt.format(value, size, self.unit)

    def __rtruediv__(self, other):
        return float(self.value) / float(other)

    def __truediv__(self, other):
        return float(self.value) / float(other)

    def __float__(self):
        return float(self.value)
