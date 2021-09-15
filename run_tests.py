#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2021
# The ptbcontrib developers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with this program.  If not, see [http://www.gnu.org/licenses/].
"""Helper script to run the test suites for ptbcontrib"""
import subprocess
import sys
from argparse import ArgumentParser
from pathlib import Path
from typing import List

from _pytest.config import ExitCode
from pygit2 import Repository

root_path = Path(__file__).parent.resolve()
ptbcontrib_path = root_path / 'ptbcontrib'
contrib_paths = [
    x for x in ptbcontrib_path.iterdir() if x.is_dir() and '__pycache__' not in x.name
]
contrib_names = [contrib.name for contrib in contrib_paths]


def get_changed_contrib_names() -> List[str]:
    """Get all changed files as compared to remote/main"""
    repo = Repository(root_path)
    main_branch = repo.lookup_branch('main')
    if main_branch is None:
        raise RuntimeError("Can't find `main` branch to compare to.")

    file_paths = (patch.delta.new_file.path for patch in repo.diff(main_branch))
    changed_contribs = set()

    for filepath in file_paths:
        if '__pycache__' not in filepath:
            path_parents = (root_path / Path(filepath)).parents
            for contrib_path in contrib_paths:
                if contrib_path in path_parents:
                    changed_contribs.add(contrib_path.name)

    return list(changed_contribs)


def run_tests(changed: bool, names: List[str]) -> int:
    """Run the required tests and install requirements for each one"""
    if changed:
        names = get_changed_contrib_names()
    elif not names:
        names = contrib_names

    failure = False
    for name in names:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(ptbcontrib_path / name / "requirements.txt"),
            ]
        )
        out = subprocess.check_call(
            [
                'pytest',
                '-v',
                '-k',
                name,
            ]
        )
        if out != ExitCode.OK:
            failure = True

    return 1 if failure else 0


if __name__ == '__main__':
    # Parse the arguments, run the tests and return exit code.

    parser = ArgumentParser(
        description=(
            'Helper script to run the tests suite for ptbcontrib. If no arguments are provided, '
            'runs tests for all contributions. At most one of the optional arguments may be used.'
            'If no optional argument is specified, will run all available test suits.'
        )
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-c',
        '--changed',
        dest='changed',
        action='store_true',
        default=False,
        help=(
            'When passed, the git diff will be checked for all files that differ from the main '
            'branch. Only the corresponding tests suits will be run.'
        ),
    )
    group.add_argument(
        '-n',
        '--names',
        dest='names',
        default=[],
        nargs='*',
        help='Use to specify the names of the contributions that you want to test.',
        choices=contrib_names,
    )

    args = parser.parse_args()
    sys.exit(run_tests(changed=args.changed, names=args.names))
