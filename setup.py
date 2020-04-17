# Copyright 2019 Google LLC <durivage@google.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup

setup(
    name='gcp-iam-member-report',
    version='1.0',
    license='Apache v2.0',
    author='Paul Durivage',
    author_email='durivage@google.com',
    description="Produces an aggregate CSV of an organization's IAM "
                "policies or a subset thereof",
    scripts=['iam_member_report.py'],
    entry_points={'console_scripts': [
        'gcp-iam-report=iam_member_report:main']},
    install_requires=[
        'google-api-python-client',
    ],
    classifiers=[
        'Programming Language :: Python :: 3.7'
        'Programming Language :: Python :: 3.6'
        'Programming Language :: Python :: 3.5'
    ]
)
