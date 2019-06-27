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

from setuptools import setup

def get_readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='d3s-nagios-plugins',
    version='0.1',
    description='Collection of various Nagios plugins',
    long_description=get_readme(),
    classifiers=[
      'Programming Language :: Python :: 3.6',
    ],
    keywords='nagios monitoring',
    url='https://lab.d3s.mff.cuni.cz/nagios-plugins/',
    install_requires=[],
    include_package_data=True,
    zip_safe=False,
    packages=[
        'd3s',
        'd3s.nagios_plugins',
    ],
    entry_points={
        'console_scripts': [
            'nagios_d3s_check_health=d3s.nagios_plugins.check_health:main',
            'nagios_d3s_check_memory=d3s.nagios_plugins.check_memory:main',
            'nagios_d3s_check_os_updates=d3s.nagios_plugins.check_os_updates:main',
            'nagios_d3s_check_systemd_service=d3s.nagios_plugins.check_systemd_service:main',
        ],
    },
)
