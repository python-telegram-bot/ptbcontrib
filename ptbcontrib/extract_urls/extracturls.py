#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020
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
"""This module contains helper functions to extract URLs from messages."""
import re
from typing import List, Dict

from telegram import MessageEntity, Message


def extract_urls(message: Message) -> List[str]:
    """
    Extracts all hyperlinks that are contained in a message. This includes message entities and the
    media caption, i.e. while of course only text *or* caption is present this works for both.
    Distinct links are returned in order of appearance.

    Note:
        For exact duplicates, only the first appearance will be kept, but there may still be URLs
        that link to the same resource.

    Args:
        message (:obj:`telegram.Message`): The message to extract from

    Returns:
        :obj:`list`: A list of URLs contained in the message
    """

    types = [MessageEntity.URL, MessageEntity.TEXT_LINK]
    results = message.parse_entities(types=types)
    results.update(message.parse_caption_entities(types=types))

    # Get the actual urls
    for key in results:
        if key.type == MessageEntity.TEXT_LINK:
            results[key] = key.url

    # Remove exact duplicates and keep the first appearance
    filtered_results: Dict[str, MessageEntity] = {}
    for key, value in results.items():
        if not filtered_results.get(value):
            filtered_results[value] = key
        else:
            if key.offset < filtered_results[value].offset:
                filtered_results[value] = key

    # Sort results by order of appearance, i.e. the MessageEntity offset
    sorted_results = sorted(filtered_results.items(), key=lambda e: e[1].offset)

    return [k for k, v in sorted_results]


def extract_message_links(
    message: Message, private_only: bool = False, public_only: bool = False
) -> List[str]:
    """
    Extracts all message links that are contained in a message. This includes message entities and
    the media caption, i.e. while of course only text *or* caption is present this works for both.
    Distinct links are returned in order of appearance.

    Note:
        For exact duplicates, only the first appearance will be kept, but there may still be URLs
        that link to the same message.

    Args:
        message (:obj:`telegram.Message`): The message to extract from
        private_only (:obj:`bool`): If ``True`` only links to messages in private groups are
            extracted. Defaults to ``False``.
        public_only (:obj:`bool`): If ``True`` only links to messages in public groups are
            extracted. Defaults to ``False``.

    Returns:
        :obj:`list`: A list of message links contained in the message
    """
    if private_only and public_only:
        raise ValueError('Only one of the optional arguments may be set to True.')

    if private_only:
        # links to private massages are of the form t.me/c/chat_id/message_id
        pattern = re.compile(r't.me/c/[0-9]+/[0-9]+')
    elif public_only:
        # links to private massages are of the form t.me/group_name/message_id
        # group names consist of a-z, 0-9 and underscore with at least 5 characters
        pattern = re.compile(r't.me/[a-z0-9_]{5,}/[0-9]+')
    else:
        pattern = re.compile(r't.me/(c/[0-9]+|[a-z0-9_]{5,})/[0-9]+')

    return [url for url in extract_urls(message) if re.search(pattern, url)]
