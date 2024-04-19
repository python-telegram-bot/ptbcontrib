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


from typing import List, Optional, Pattern, Union, Any, Callable

from telegram.ext import Application, CallbackQueryHandler, ChatMemberHandler, InlineQueryHandler
from telegram.ext import filters as filters_module
from telegram.ext.filters import BaseFilter

from .handlers import NewCommandHandler as CommandHandler
from .handlers import NewMessageHandler as MessageHandler


class TelegramHandler:
    """
    A class that provides decorators for registering command, message, callback query, inline query and chat member update handlers.
    """

    def __init__(self, application: Application) -> None:
        self.app = application

    def command(
        self,
        command: List[str],
        filters: Optional[filters_module.BaseFilter] = None,
        block: Optional[bool] = True,
        has_args: Optional[Union[bool, int]] = None,
        group: Optional[int] = 0,
        allow_edit: Optional[Union[bool, bool]] = False,
        prefix: Optional[List] = None,
    ) -> Callable[[Any], None]:
        """
        Decorator for registering a command handler with the Telegram Bot API.

        Returns:
            function: Decorated command.

            @param command:
            @param filters:
            @param block:
            @param has_args:
            @param group:
            @param allow_edit:
            @param prefix:
        """
        if allow_edit:
            filters = filters
        elif filters:
            filters = filters & ~filters_module.UpdateType.EDITED_MESSAGE
        else:
            filters = ~filters_module.UpdateType.EDITED_MESSAGE

        def _command(func) -> None:
            self.app.add_handler(
                CommandHandler(
                    command,
                    func,
                    filters=filters,
                    block=block,
                    has_args=has_args,
                    prefix=prefix,
                ),
                group,
            )
            return func

        return _command

    def message(
        self,
        filters: BaseFilter | None,
        block: Optional[bool] = True,
        allow_edit: Optional[Union[bool, bool]] = False,
        group: Optional[int] = 0,
    ) -> Callable[[Any], None]:
        """
        Decorator for registering a message handler with the Telegram Bot API.

        Returns:
            function: Decorated message.
            @param filters:
            @param block:
            @param allow_edit:
            @param group:
        """

        def _message(func) -> None:
            self.app.add_handler(
                MessageHandler(filters=filters, callback=func, block=block, allow_edit=allow_edit),
                group,
            )
            return func

        return _message

    def callback_query(
        self, pattern: str = None,
        block: Optional[bool] = True
    ) -> Callable[[Any], None]:
        """
        Decorator for registering a callback query handler with the Telegram Bot API.

        Returns:
            function: Decorated callback query.

            @param pattern:
            @param block:
        """

        def _callback_query(func) -> None:
            self.app.add_handler(CallbackQueryHandler(callback=func, pattern=pattern, block=block))
            return func

        return _callback_query

    def inline_query(
        self,
        pattern: Optional[Union[str, Pattern[str]]] = None,
        block: Optional[bool] = True,
        chat_types: Optional[List[str]] = None,
    ) -> Callable[[Any], None]:
        """
        Decorator for registering an inline query handler with the Telegram Bot API.

        Returns:
            function: Decorated inline query.

            @param pattern:
            @param block:
            @param chat_types:
        """

        def _inline_query(func) -> None:
            self.app.add_handler(
                InlineQueryHandler(
                    callback=func,
                    pattern=pattern,
                    block=block,
                    chat_types=chat_types
                )
            )
            return func

        return _inline_query

    def chat_member(
        self,
        chat_member_types: int = -1,
        block: Optional[bool] = True,
        group: Optional[int] = 0,
    ) -> Callable[[Any], None]:
        """Decorator for handle Telegram updates that contain a chat member update.

        Returns:
            function: Decorated chat member.

            @param chat_member_types:
            @param block:
            @param group:
        """

        def _chat_member(func) -> None:
            self.app.add_handler(ChatMemberHandler(func, chat_member_types, block), group)
            return func

        return _chat_member
