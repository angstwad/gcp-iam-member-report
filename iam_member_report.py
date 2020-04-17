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

# https://github.com/googleapis/google-auth-library-python/issues/271
import warnings

warnings.filterwarnings(
    "ignore",
    "Your application has authenticated using end user credentials"
)

import sys
import argparse
import csv
import pathlib
import typing

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class LazyFileType(argparse.FileType):
    """
    Subclasses `argparse.FileType` in order to provide a way to lazily open
    files for reading/writing from arguments.  Initializes the same as the
    parent, but provides `open` method which returns the file object.
    Usage:
    ```
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', type=LazyFileType('w'))
    args = parser.parse_args()
    with args.f.open() a f:
        for line in foo:
            ...
    ```
    Provides an alternate constructor for use with the `default` kwarg to
    `ArgumentParser.add_argument`.
    Usage:
    ```
    #
    parser.add_argument('-f',
                        type=LazyFileType('w'),
                        default=LazyFileType.default('some_file.txt', mode='w')
    """

    def __call__(self, string: str):
        self.filename = string

        if 'r' in self._mode or 'x' in self._mode:
            if not pathlib.Path(self.filename).exists():
                m = (f"can't open {self.filename}:  No such file or directory: "
                     f"'{self.filename}'")
                raise argparse.ArgumentTypeError(m)

        return self

    def open(self) -> typing.IO:
        return open(self.filename, self._mode, self._bufsize, self._encoding,
                    self._errors)

    @classmethod
    def default(cls, string: str, **kwargs):
        inst = cls(**kwargs)
        inst.filename = string
        return inst


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('org_id', help='Organization ID')
    parser.add_argument('-f', '--folder', help='Restrict search to folder')
    parser.add_argument('-o', '--output',
                        type=LazyFileType('w'),
                        default=LazyFileType.default('iam_members.csv',
                                                     mode='w'),
                        help='File to write results. Default: iam_members.csv')
    return parser.parse_args()


def run(org_id, folder_id, outfile):
    _ERROR = None
    crm_v1 = build('cloudresourcemanager', 'v1')
    crm_v2 = build('cloudresourcemanager', 'v2')

    print('Validating organization...')
    request = crm_v1.organizations().get(name=f'organizations/{org_id}')
    try:
        org = request.execute()
    except HttpError as e:
        raise SystemExit(f'Error getting organization: {e}')

    # gets _all_ projects visible with current creds
    # would be better if project search API call was available
    # TODO: find if server-side filtering can limit to projects in hierarchy
    projects = []
    request = crm_v1.projects().list()
    while request:
        print('Getting projects...')
        response = request.execute()
        projects.extend(response.get('projects', []))
        request = crm_v1.projects().list_next(previous_request=request,
                                              previous_response=response)

    final_results = []

    # set the parent node
    if folder_id:
        parent = f'folders/{folder_id}'
    else:
        parent = org['name']

        # since the parent is the org, get the org IAM policy
        request = crm_v1.organizations().getIamPolicy(resource=org['name'])
        try:
            iam = request.execute()
        except HttpError as e:
            _ERROR = True
            m = f'Error getting org folder "{folder_id}" IAM policy: {e}'
            print(m, file=sys.stderr)
        else:
            for binding in iam.get('bindings', []):
                for member in binding.get('members', []):
                    typ, mem = member.split(':')
                    r = (mem, typ, binding['role'], org_id, '', '')
                    final_results.append(r)

    folders = set()
    stack = [parent]

    # walk folders, getting IAM policies along the way
    while stack:
        current = stack.pop()
        request = crm_v2.folders().list(parent=current)
        while request:
            print('Getting folders...')
            try:
                response = request.execute()
            except HttpError as e:
                _ERROR = True
                m = f'Error getting child folders of "{current}": {e}'
                print(m, file=sys.stderr)
                continue

            for folder in response.get('folders', []):
                fname = folder['name']
                fid = fname.split('/')[1]
                stack.append(folder['name'])
                folders.add(fid)

                req = crm_v2.folders().getIamPolicy(resource=folder['name'])

                try:
                    iam = req.execute()
                except HttpError as e:
                    _ERROR = True
                    print(f'Error getting folder "{fid} IAM: {e}')
                    continue

                for binding in iam.get('bindings', []):
                    for member in binding.get('members', []):
                        typ, mem = member.split(':')
                        r = (mem, typ, binding['role'], '', fid, '')
                        final_results.append(r)

            request = crm_v2.folders().list_next(previous_request=request,
                                                 previous_response=response)

    # process project-level IAM
    print('Processing results...')
    for project in projects:
        parent = project.get('parent', {})
        pid = project['projectId']

        # get IAM policy for folders, but only if they're active and have
        # parents in the walked org hierarchy
        if (project['lifecycleState'].lower() == 'active' and
                (parent.get('id') == org_id or parent.get('id') in folders)):

            req = crm_v1.projects().getIamPolicy(resource=pid)
            try:
                iam = req.execute()
            except HttpError as e:
                _ERROR = True
                print(f'Error getting project IAM: {e}', file=sys.stderr)
                continue

            for binding in iam.get('bindings', []):
                for member in binding.get('members', []):
                    typ, mem = member.split(':')
                    r = (mem, typ, binding['role'], '', '', pid)
                    final_results.append(r)

    print(f'Writing file "{outfile.filename}"')
    with outfile.open() as f:
        writer = csv.writer(f)
        writer.writerow(('member', 'member_type', 'role',
                         'org_id', 'folder_id', 'project_id'))
        writer.writerows(final_results)

    print('Done.')

    if _ERROR:
        print('There were errors while generating the report; it may not be '
              'completely accurate.')

    return _ERROR


def main():
    args = parse_args()
    sys.exit(run(args.org_id, args.folder, args.output))


if __name__ == '__main__':
    main()
