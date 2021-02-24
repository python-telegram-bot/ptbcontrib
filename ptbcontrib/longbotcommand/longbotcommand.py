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
"""
This module contains a subclass for the BotCommand class
that allows for a longer description (e. g. for /help purposes).
"""
from telegram import BotCommand


class LongBotCommand(BotCommand):
    """
    Allows for a longer description (>256 characters) to be stored alongside
    the shorter one allowed for :class:`telegram.BotCommand` by Telegram's API limit.
    Passing this to `set_my_commands` ignores `long_bot_description`.

    Args:
        command (:obj:`str`): The command's handle, pass exactly like
            handle to :class:`telegram.BotCommand`
        description (:obj:`str`): The command's description, pass exactly like
            description to :class:`telegram.BotCommand`
        long_description (:obj:`str`, optional): The command's longer description,
            pass like description to :class:`telegram.BotCommand`. Defaults to ``None``,
            in which case the short description is duplicated as the long one.

    Attributes:
        long_description (:obj:`str`): The command's longer description.
    """

    def __init__(self, command: str, description: str, long_description: str = None) -> None:
        # parent class BotCommand is initializaed with required parameters
        super().__init__(command, description)
        # private attribute, as per suggestion
        self._long_description = long_description

    @property
    def long_description(self) -> str:
        """
        Returns the appropriate description (long if provided on init, short otherwise)
        """

        # if long_description was specified, use it as the long description
        if self._long_description is not None:
            return self._long_description
        # if long_description wasn't specified, use the short description
        return self.description
