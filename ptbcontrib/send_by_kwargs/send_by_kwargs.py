#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2023
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
"""This module contains a helper function that allows to send any kind of message by kwargs."""
import inspect
from collections import OrderedDict
from typing import Callable, Dict, List, Union

from telegram import Bot, Message

_UNIQUE_KWARGS = OrderedDict(
    {
        "send_animation": ["animation"],
        "send_audio": ["audio"],
        "send_chat_action": ["action"],
        "send_contact": ["phone_number", "contact"],
        "send_document": ["document"],
        "send_game": ["game_short_name"],
        "send_invoice": ["prices"],
        # venue must be before location as location has all args of venue, but not vice versa
        "send_venue": ["address", "venue"],
        "send_location": ["latitude", "location"],
        "send_media_group": ["media"],
        "send_message": ["text"],
        "send_photo": ["photo"],
        "send_poll": ["question"],
        "send_sticker": ["sticker"],
        "send_video": ["video"],
        "send_video_note": ["video_note"],
        "send_voice": ["voice"],
        # Important to test last, as this only requires chat_id
        "send_dice": ["chat_id"],
    }
)

_CACHED_SIGNATURES: Dict[str, inspect.Signature] = {}


class _MissingRequiredParam(Exception):
    """Auxiliary Exception class for internal usage."""

    def __init__(self, param_name: str):
        super().__init__()
        self.param_name = param_name


def _get_relevant_kwargs(method: Callable, kwargs: Dict[str, object]) -> Dict[str, object]:
    """
    Extracts the kwargs relevant for the method at hand. For internal usage.
    """
    signature = _CACHED_SIGNATURES.setdefault(method.__name__, inspect.signature(method))
    relevant_kwargs = {}
    for name, param in signature.parameters.items():
        if param.default == inspect.Parameter.empty and name not in kwargs:
            raise _MissingRequiredParam(name)
        # we don't just do kwargs.get(name, None) here to make sure
        # that this still works with telegram.ext.Defaults
        if name in kwargs:
            relevant_kwargs[name] = kwargs[name]
    return relevant_kwargs


async def send_by_kwargs(
    bot: Bot, kwargs: Dict[str, object] = None, **_kwargs: object
) -> Union[Message, List[Message]]:
    """
    Convenience method for sending arbitrary messages by providing the corresponding keywords.
    Auto-selects the corresponding bot method. For flexibility, arguments can be passed both by
    passing a dict and by specifying them directly as keyword arguments::

        send_by_kwargs(bot, kwargs={'text'='Hi'}, chat_id=123)

    Note:
        Keyword arguments passed directly will override those passed in the dictionary ``kwargs``.

    Args:
        bot (:class:`telegram.Bot`): The bot to send the message with.
        kwargs (Dict[:obj:`str`, :obj:`object`], optional): The keyword arguments as dictionary.
        **_kwargs (Dict[:obj:`str`, :obj:`object`], optional): Additional keyword arguments passed
            as actual keyword arguments.

    Returns:
        :class:`telegram.Message` | List[:class:`telegram.Message`]:

    Raises:
        KeyError | RuntimeError: KeyError, if a suitable method was selected, but it's missing a
            required parameter. RuntimeError, if no method could be selected or the selected method
            raised an exception.
    """
    if kwargs is None:
        kwargs = {}
    kwargs.update(_kwargs)

    for method_name, unique_kwarg in _UNIQUE_KWARGS.items():
        if any(kwargs.get(uk, None) is not None for uk in unique_kwarg):
            selected_method = method_name
            break
    else:
        raise RuntimeError("Could not find a bot method to call for the passed kwargs.")

    try:
        method = getattr(bot, selected_method)
        relevant_kwargs = _get_relevant_kwargs(method, kwargs)
    except _MissingRequiredParam as exc:
        raise KeyError(
            f"Selected method {method.__name__!r}, but the required parameter "
            f"{exc.param_name!r} is missing in the provided kwargs."
        ) from exc

    try:
        return await method(**relevant_kwargs)
    except Exception as exc:
        raise RuntimeError(
            f"Selected method {method.__name__!r}, but it raised the above exception."
        ) from exc
