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

from __future__ import annotations

import re

import pytest
from telegram import InlineKeyboardButton as Ikb
from telegram import InlineKeyboardMarkup as Ikm

from ptbcontrib.extended_keyboards.select_keyboards import (
    Exceptions,
    SelectAllButton,
    SelectButton,
    SelectKeyboard,
    SimpleButton,
    SimpleButtonManager,
)

ikb_select_1 = Ikb(
    text="+Button text",
    callback_data="original callback SELECT_BTN 0 + - 1",
)
ikb_select_2 = Ikb(
    text="-Button text",
    callback_data="original callback SELECT_BTN 0 + - 0",
)
ikb_1 = Ikb(
    text="Non convertable button",
    callback_data="Do no matching the select pattern",
)
ikb_2 = Ikb(
    text="Non convertable button",
    callback_data="Do no matching the select pattern",
)
ikb_row = (
    ikb_1,
    ikb_2,
)
select_button_1 = SelectButton(
    is_selected=True,
    checkbox_position=0,
    checked_symbol="+",
    unchecked_symbol="-",
    text="Button text",
    callback_data="original callback",
)
select_button_2 = SelectButton(
    is_selected=False,
    checkbox_position=0,
    checked_symbol="+",
    unchecked_symbol="-",
    text="Button text",
    callback_data="original callback",
)
select_all_button_true = SelectAllButton(
    is_selected=True,
    checkbox_position=0,
    checked_symbol="+",
    unchecked_symbol="-",
    text="Select all",
    callback_data="original callback",
)
select_all_button_false = select_all_button_true.invert()
simple_button = SimpleButton(
    is_selected=True,
    text="Button text",
    callback_data="original callback",
)
simple_button_manager = SimpleButtonManager(
    text="Button text",
    callback_data="original callback",
)
ikm = Ikm(
    inline_keyboard=(
        (
            ikb_select_1,
            ikb_select_2,
        ),
        (
            ikb_1,
            ikb_2,
        ),
        (
            select_button_1,
            select_button_2,
        ),
        (select_all_button_false,),
    ),
)
select_ikm = SelectKeyboard(
    inline_keyboard=(
        (
            select_button_1,
            select_button_2,
        ),  # Converted row of ikb_select buttons
        (
            ikb_1,
            ikb_2,
        ),
        (select_button_1, select_button_2),
        (select_all_button_false,),
    ),
)


class TestSelectButtonBase:

    @staticmethod
    def test_is_select_button():
        assert (
            SelectButton.is_convertable(
                button=select_button_1,
            )
            is False
        )
        assert (
            SelectButton.is_convertable(
                button=ikb_select_1,
            )
            is True
        )
        assert (
            SelectButton.is_convertable(
                button=ikb_1,
            )
            is False
        )

    class TestInvertText:
        """test_invert_text"""

        @staticmethod
        def test_checked_longer():
            select_button = SelectButton(
                is_selected=True,
                checkbox_position=2,
                checked_symbol="+++",
                unchecked_symbol="--",
                text="123456789",
            )
            result = select_button.invert_text()
            assert result == "12--3456789"

        @staticmethod
        def test_unchecked_longer():
            select_button = SelectButton(
                is_selected=False,
                checkbox_position=0,
                checked_symbol="+++",
                unchecked_symbol="------",
                text="123456789",
            )
            result = select_button.invert_text()
            assert result == "+++123456789"

        @staticmethod
        def test_selected_empty_checked_text():
            select_button = SelectButton(
                is_selected=True,
                checkbox_position=5,
                checked_symbol="",
                unchecked_symbol="--",
                text="123456789",
            )
            result = select_button.invert_text()
            assert result == "12345--6789"

        @staticmethod
        def test_selected_empty_unchecked_text():
            select_button = SelectButton(
                is_selected=True,
                checkbox_position=5,
                checked_symbol="+",
                unchecked_symbol="",
                text="123456789",
            )
            result = select_button.invert_text()
            assert result == "123456789"

    @staticmethod
    def test_invert_callback_data():
        select_btn = SelectButton(
            is_selected=True,
            checkbox_position=0,
            checked_symbol="+",
            unchecked_symbol="-",
            text="foo",
            callback_data="bar",
        )
        result = select_btn.invert_callback_data()
        assert result == "bar SELECT_BTN 0 + - 0"

    @staticmethod
    def test_invert():
        result = select_button_1.invert()
        expected = SelectButton(
            is_selected=False,
            checkbox_position=select_button_1.checkbox_position,
            checked_symbol=select_button_1.checked_symbol,
            unchecked_symbol=select_button_1.unchecked_symbol,
            text="Button text",
            callback_data="original callback",
        )
        assert result == expected

    class TestFromInline:
        """test_from_inline"""

        @staticmethod
        def test_success():
            """Convert back"""
            result = SelectButton.from_inline(
                button=ikb_select_1,
            )
            assert result == select_button_1

        @staticmethod
        def test_already_converted():
            """Convert back"""
            result = SelectButton.from_inline(
                button=select_button_1,
            )
            assert result == select_button_1

        @staticmethod
        def test_not_select_button():
            """Convert back"""
            with pytest.raises(Exceptions.NotConvertable):
                SelectButton.from_inline(
                    button=ikb_1,
                )


class TestSelectAllButton:
    @staticmethod
    def test_update():
        result = select_all_button_true.update(
            keyboard=ikm.inline_keyboard,
        )
        assert result == select_all_button_false

    @staticmethod
    def test_resolve_is_selected():
        result = SelectAllButton.resolve_is_selected(
            keyboard=ikm.inline_keyboard,
        )
        assert result is False


class TestSelectKeyboard:

    @staticmethod
    def test_convert_inline_buttons():
        keyboard = SelectKeyboard(
            inline_keyboard=(
                (
                    simple_button,
                    simple_button_manager,
                ),
                (
                    ikb_1,
                    ikb_select_1,
                ),
            ),
        )
        assert keyboard.inline_keyboard == (
            (
                SelectButton(
                    is_selected=True,
                    checkbox_position=SelectKeyboard.CHECKBOX_POSITION,
                    checked_symbol=SelectKeyboard.CHECKED_SYMBOL,
                    unchecked_symbol=SelectKeyboard.UNCHECKED_SYMBOL,
                    text="Button text",
                    callback_data="original callback",
                ),
                SelectAllButton(
                    is_selected=True,
                    checkbox_position=SelectKeyboard.CHECKBOX_POSITION,
                    checked_symbol=SelectKeyboard.CHECKED_SYMBOL,
                    unchecked_symbol=SelectKeyboard.UNCHECKED_SYMBOL,
                    text="Button text",
                    callback_data="original callback",
                ),
            ),
            (
                ikb_1,
                select_button_1,
            ),
        )

    @staticmethod
    def test_extract_select_buttons():
        result = SelectKeyboard.extract_select_buttons(
            inline_keyboard=ikm.inline_keyboard,
        )
        assert result == [select_button_1, select_button_2]

    @staticmethod
    def test_is_all_buttons_selected():
        keyboard = Ikm(
            inline_keyboard=(
                (
                    select_button_1,
                    ikm,
                ),
                (select_button_1, ikb_select_1),
            ),
        )
        result = SelectKeyboard.is_all_buttons_selected(
            inline_keyboard=keyboard.inline_keyboard,
        )
        assert result is True
        result = SelectKeyboard.is_all_buttons_selected(
            inline_keyboard=ikm.inline_keyboard,
        )
        assert result is False

    class TestFindBtn:
        """test_find_btn"""

        @staticmethod
        def test_pattern():
            result = SelectKeyboard.find_btn(
                inline_keyboard=ikm.inline_keyboard,
                pattern=re.compile(
                    re.escape(
                        ikb_select_1.callback_data,
                    )
                ),
            )
            assert result == (ikb_select_1, 0, 0)

        @staticmethod
        def test_str():
            result = SelectKeyboard.find_btn(
                inline_keyboard=ikm.inline_keyboard,
                pattern=ikb_select_1.callback_data,
            )
            assert result == (ikb_select_1, 0, 0)

    @staticmethod
    @pytest.mark.parametrize(
        argnames=(
            "flag",
            "index",
        ),
        argvalues=(
            (
                True,
                1,
            ),
            (False, 0),
        ),
    )
    def test_set_all_buttons(
        flag: bool,
        index: int,
    ):
        """
        All buttons (1 of 2 in this keyboard) was inverted to required value
        Note: first row is convertable but not inverted as not `SelectButton` instance
        """
        result = SelectKeyboard.set_all_buttons(
            keyboard=ikm.inline_keyboard,
            flag=flag,
        )
        expected = [list(row) for row in ikm.inline_keyboard]
        expected[2][index] = (
            select_button_1,
            select_button_2,
        )[index].invert()
        assert result == expected

    class TestFromInline:
        """test_from_inline"""

        @staticmethod
        def test_inline_keyboard():
            """1 of 2 in this keyboard was inverted to required value"""
            result = SelectKeyboard.from_inline(
                keyboard=ikm.inline_keyboard,
            )
            assert result == [list(row) for row in select_ikm.inline_keyboard]

        @staticmethod
        def test_keyboard():
            """1 of 2 in this keyboard was inverted to required value"""
            result = SelectKeyboard.from_inline(
                keyboard=ikm,
            )
            assert result == select_ikm

    class TestInvertByCallback:

        @staticmethod
        def test_all_button():
            expected = [
                # Converted ikb_select buttons
                [
                    select_button_1,
                    select_button_1,
                ],  # Inverted by select all button
                [
                    ikb_1,
                    ikb_1,
                ],
                [select_button_1, select_button_1],  # Inverted by select all button
                [
                    select_all_button_false.invert(),
                ],
            ]
            result = SelectKeyboard.invert_by_callback(
                cbk_data=select_all_button_false.callback_data,
                keyboard=ikm.inline_keyboard,
            )
            assert result == expected

        @staticmethod
        def test_select_button():
            expected = SelectKeyboard(
                inline_keyboard=(
                    (  # Converted row of ikb_select buttons
                        select_button_1.invert(),  # Inverted first found select button
                        select_button_2,
                    ),
                    (
                        ikb_1,
                        ikb_2,
                    ),
                    (select_button_1, select_button_2),
                    (select_all_button_false,),
                ),
            )
            result = SelectKeyboard.invert_by_callback(
                cbk_data=ikb_select_1.callback_data,
                keyboard=ikm,
            )
            assert result == expected

        @staticmethod
        def test_not_select_button():
            assert (
                SelectKeyboard.invert_by_callback(
                    cbk_data="This is not matching any pattern SELECT_BTN 0 + - 1",
                    keyboard=ikm,
                )
                is None
            )
