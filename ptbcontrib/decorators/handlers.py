#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2024
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

from typing import Any, Dict, List, Optional, Tuple, Union

import telegram.ext as tg
from telegram import Update
from telegram._utils.defaultvalue import DEFAULT_TRUE
from telegram._utils.types import DVType
from telegram.ext import filters as filters_module
from telegram.ext._utils.types import FilterDataDict


class CustomCommandHandler(tg.CommandHandler):
    def __init__(
        self,
        command: Union[str, list],
        callback,
        prefix: Optional[List] = None,
        **kwargs,
    ):
        if prefix is None:
            prefix = ["/", "!"]
        super().__init__(command, callback, **kwargs)
        self.PREFIX = prefix

        if isinstance(command, str):
            frozenset({command.lower()})
        else:
            frozenset(x.lower() for x in command)

    def check_update(
        self, update: object
    ) -> Optional[Union[bool, Tuple[List[str], Optional[Union[bool, FilterDataDict]]]]]:

        if isinstance(update, Update) and update.effective_message:
            message = update.effective_message

            if message.text and len(message.text) > 1:
                fst_word = message.text.split(None, 1)[0]
                if len(fst_word) > 1 and any(
                    fst_word.startswith(start) for start in self.PREFIX
                ):
                    args = message.text.split()[1:]
                    command_parts = fst_word[1:].split("@")
                    command_parts.append(message.get_bot().username)

                    if (
                        command_parts[0].lower() not in self.commands
                        or command_parts[1].lower()
                        != message.get_bot().username.lower()
                    ):
                        return None

                    if not self._check_correct_args(args):
                        return None

                    if filter_result := self.filters.check_update(update):
                        return args, filter_result
                    return False
        return None


class CustomMessageHandler(tg.MessageHandler):
    def __init__(
        self,
        filters,
        callback,
        block: DVType[bool] = DEFAULT_TRUE,
        allow_edit=False,
        **kwargs,
    ):
        super().__init__(filters, callback, block=block)
        if allow_edit is False:
            self.filters &= ~(
                filters_module.UpdateType.EDITED_MESSAGE
                | filters_module.UpdateType.EDITED_CHANNEL_POST
            )

        def check_update(
            self, update: object
        ) -> Optional[Union[bool, Dict[str, List[Any]]]]:
            if isinstance(update, Update):
                return self.filters.check_update(update) or False
            return None


tg.CommandHandler = CustomCommandHandler
tg.MessageHandler = CustomMessageHandler
