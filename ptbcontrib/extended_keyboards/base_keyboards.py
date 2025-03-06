#!/usr/bin/env python
#
# A library containing community-based extension for the python-telegram-bot library
# Copyright (C) 2020-2025
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

"""This module contains extended keyboard classes with extra functionality for PTB keyboards."""

from __future__ import annotations

from abc import ABC, abstractmethod

# isort: off
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


class Exceptions:
    """Just a data container"""

    class NotEnoughButtons(
        Exception,
    ):
        """Exception raised when there are not enough buttons to fill the keyboard."""

        def __init__(
            self,
            inline_keyboard: tuple[tuple[InlineKeyboardButton, ...], ...],
            buttons: list[InlineKeyboardButton,],
            buttons_in_row: int,
        ) -> None:
            super().__init__(
                "Total count of buttons not enough to fill the keyboard by equal rows "
                f"({len(buttons)} collected and "
                f"{buttons_in_row * len(inline_keyboard, )} required."
            )

    class EmptyRowsDisallowed(
        Exception,
    ):
        """Exception raised when empty rows are not allowed in the keyboard."""

        def __init__(
            self,
        ) -> None:
            super().__init__("Result num of rows less that original num of rows in the keyboard.")


class IExtendedInlineKeyboardMarkup(
    ABC,
):
    """Popular keyboard actions"""

    @abstractmethod
    def to_list(
        self,
    ) -> list[list[InlineKeyboardButton]]:
        """Just convert to list. By default, inline_keyboard is tuple[tuple[...]]"""

    @abstractmethod
    def find_btn_by_cbk(
        self,
        cbk: str,
        strict: bool = True,
    ) -> tuple[InlineKeyboardButton, int, int] | None:
        """Returns buttons, row index, column index if found, None otherwise"""

    @abstractmethod
    def get_buttons(
        self,
    ) -> list[InlineKeyboardButton]:
        """Just get flat list of buttons of the keyboard"""

    @abstractmethod
    def split(
        self,
        buttons_in_row: int,
        empty_rows_allowed: bool = True,
        strict: bool = False,
    ) -> list[list[InlineKeyboardButton]]:
        """
        Split keyboard by N buttons in row.
        Last row will contain remainder,
        i.e. num of buttons in the last row maybe less than `buttons_in_row` parameter.

        Possible enhancement:
            keep_empty_rows: bool - keep empty rows in final keyboard if not enough buttons.
            # Please create feature issue if you need it.
        """


class ExtendedInlineKeyboardMarkup(
    InlineKeyboardMarkup,
    IExtendedInlineKeyboardMarkup,
):
    """Popular keyboard actions"""

    def to_list(
        self,
    ) -> list[list[InlineKeyboardButton]]:
        """Just convert to list. By default, inline_keyboard is tuple[tuple[...]]"""
        list_keyboard = [list(row) for row in self.inline_keyboard]
        return list_keyboard

    def find_btn_by_cbk(
        self,
        cbk: str,
        strict: bool = True,
    ) -> tuple[InlineKeyboardButton, int, int] | None:
        """
        Returns buttons, row index, column index if found, None otherwise
        Note: only string callback data supported for `InlineKeyboardButton`.
        """
        for row_index, row in enumerate(self.inline_keyboard):
            for column_index, _ in enumerate(row):
                button = self.inline_keyboard[row_index][column_index]  # alias
                if not isinstance(
                    button.callback_data,
                    str,
                ):
                    continue  # Only string callback data supported
                if strict:
                    check_result = cbk == button.callback_data
                else:  # "in" to keep ability to match by prefix and some cbk key
                    check_result = cbk in button.callback_data
                if check_result:
                    return button, row_index, column_index
        return None

    def get_buttons(
        self,
    ) -> list[InlineKeyboardButton]:
        """Just get flat list of buttons of the keyboard"""
        result = []
        for row in self.inline_keyboard:
            for btn in row:
                result.append(btn)
        return result

    def split(
        self,
        buttons_in_row: int,
        empty_rows_allowed: bool = True,
        strict: bool = False,
    ) -> list[list[InlineKeyboardButton]]:
        """
        Split keyboard by N buttons in row.
        Last row will contain remainder,
        i.e. num of buttons in the last row maybe less than `buttons_in_row` parameter.
        ((button_1, ), (button_2, )) -> ((button_1, button_2, ), )

        Usage:
        button_1 = InlineKeyboardButton(...)
        button_2 = InlineKeyboardButton(...)
        extended_keyboard = ExtendedInlineKeyboardMarkup(
        inline_keyboard=((button_1, ), (button_2, )),
        )
        new_inline_keyboard = extended_keyboard.split(  # -> ((button_1, button_2, ), )
            buttons_in_row = 2,
            #  empty_rows_allowed=True  # If some rows should be filled later by user.
            #  strict=True  # If Every row should contain exactly 2 (buttons_in_row) buttons.
        )
        Possible enhancement:
            keep_empty_rows: bool - keep empty rows in final keyboard if not enough buttons.
            # Please create feature issue if you need it.
        """

        if buttons_in_row < 1:
            raise ValueError("`buttons_in_row` parameter should be positive (>= 1).")

        buttons = self.get_buttons()

        if strict and len(buttons) < buttons_in_row * len(
            self.inline_keyboard,  # num of rows
        ):
            raise Exceptions.NotEnoughButtons(
                inline_keyboard=self.inline_keyboard,
                buttons=buttons,
                buttons_in_row=buttons_in_row,
            )

        new_keyboard = []
        for i in range(0, len(buttons), buttons_in_row):
            new_keyboard.append(buttons[i : i + buttons_in_row])  # noqa: E203

        if not empty_rows_allowed and len(new_keyboard) < len(
            self.inline_keyboard,
        ):
            raise Exceptions.EmptyRowsDisallowed

        return new_keyboard
