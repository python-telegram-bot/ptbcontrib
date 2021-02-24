#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2021
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
import subprocess

import pytest
import sys

from telegram import BotCommand
from ptbcontrib.longbotcommand import LongBotCommand


@pytest.fixture(scope='module', autouse=True)
def install_requirements():
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "ptbcontrib/longbotcommand/requirements.txt",
        ]
    )


@pytest.fixture(scope='function')
def bot_command():
    return BotCommand(command='test', description='desc')


@pytest.fixture(scope='function')
def short_desc_command():
    return LongBotCommand(command='test', description='desc')


@pytest.fixture(scope='function')
def long_desc_command():
    return LongBotCommand(command='test', description='desc', long_description='long desc')


class TestLongBotCommand:
    def test_short_desc_init(self, short_desc_command):
        assert short_desc_command.command == 'test'
        assert short_desc_command.description == 'desc'
        assert short_desc_command.long_description == 'desc'

    def test_long_desc_init(self, long_desc_command):
        assert long_desc_command.command == 'test'
        assert long_desc_command.description == 'desc'
        assert long_desc_command.long_description == 'long desc'

    def test_short_desc_change(self, short_desc_command):
        short_desc_command.description = 'new desc'
        assert short_desc_command.long_description == 'new desc'

    def test_long_desc_change(self, long_desc_command):
        long_desc_command.description = 'new desc'
        assert long_desc_command.long_description == 'long desc'

    def test_short_desc_dict(self, short_desc_command, bot_command):
        assert short_desc_command.to_dict() == bot_command.to_dict()

    def test_long_desc_dict(self, long_desc_command, bot_command):
        assert long_desc_command.to_dict() == bot_command.to_dict()

    def test_short_desc_json(self, short_desc_command, bot_command):
        assert short_desc_command.to_json() == bot_command.to_json()

    def test_long_desc_json(self, long_desc_command, bot_command):
        assert long_desc_command.to_json() == bot_command.to_json()
