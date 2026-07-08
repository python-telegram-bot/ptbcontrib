# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2026
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
This module contains a filter that filters correctly in a group with topics.
"""

from .true_reply_filter import TRUE_REPLY_FILTER

__all__ = [
    "TRUE_REPLY_FILTER",
]
