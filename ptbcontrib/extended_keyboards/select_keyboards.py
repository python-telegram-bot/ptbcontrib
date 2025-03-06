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

"""This module implement checkbox buttons for PTB inline keyboard"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, ClassVar, Sequence, overload

from telegram import InlineKeyboardButton as Ikb
from telegram import InlineKeyboardMarkup as Ikm

if TYPE_CHECKING:
    from telegram import CallbackGame, LoginUrl, SwitchInlineQueryChosenChat, WebAppInfo
    from telegram._utils.types import JSONDict
    from typing_extensions import Self

CHECKED_SYMBOL = "☑"
UNCHECKED_SYMBOL = "🔲"


class Exceptions:
    """Container class with the module logic exceptions"""

    class NotConvertable(Exception):
        """Raised when trying to convert an `InlineKeyboardButton` that is not convertible"""

        def __init__(self) -> None:
            super().__init__(
                "Passed instance of `InlineKeyboardButton` is not convertable,"
                "Please use the is_convertible method first to check "
                "if the callback_data has the appropriate format."
            )


@dataclass(
    slots=True,
)
class SelectButtonBaseFields:
    """Fields that `SelectButton` are represents and created for"""

    CHECKED_SYMBOL: ClassVar[str] = CHECKED_SYMBOL
    UNCHECKED_SYMBOL: ClassVar[str] = UNCHECKED_SYMBOL

    checkbox_position: int = 0
    checked_symbol: str = CHECKED_SYMBOL
    unchecked_symbol: str = UNCHECKED_SYMBOL


@dataclass(
    slots=True,
    kw_only=True,
)
class IkbStruct:  # pylint: disable=too-many-instance-attributes
    """The same as InlineKeyboardButton but with additional select fields."""

    text: str
    callback_data: str
    url: str | None = None
    switch_inline_query: str | None = None
    switch_inline_query_current_chat: None | str | None = None
    callback_game: CallbackGame | None = None
    pay: bool | None = None
    login_url: LoginUrl | None = None
    web_app: WebAppInfo | None = None
    switch_inline_query_chosen_chat: SwitchInlineQueryChosenChat | None = None
    api_kwargs: JSONDict | None = None


@dataclass(
    slots=True,
    kw_only=True,
)
class SelectButtonStruct(
    SelectButtonBaseFields,
):
    """
    The same as InlineKeyboardButton with additional SelectButton fields.
    Note: no `is_selected` parameter yet.
    """


class SelectButtonBase(
    Ikb,
    ABC,
):
    """
    Button that represents button with checkboxes, extends the `InlineKeyboardButton`,
    and provides convenience methods to manage button state
    (note: button state is immutable according to PTB objects management policy,
    so most of the methods returns new state).
    """

    SELECT_BTN_S = "SELECT_BTN"
    SELECT_BTN_R = re.compile(
        rf".* ({SELECT_BTN_S}) (\d+) (\S+) (\S+) ([01])$",
    )

    @property
    def is_selected(self) -> bool:
        """Whether the button is selected."""
        return self.callback_data[-1] == "1"

    # pylint: disable=R0917, R0913, R0914
    def __init__(
        self,
        text: str,
        is_selected: bool,
        checkbox_position: int = 0,
        checked_symbol: str = CHECKED_SYMBOL,
        unchecked_symbol: str = UNCHECKED_SYMBOL,
        transform: bool = True,
        url: str | None = None,
        callback_data: str | object | None = None,
        switch_inline_query: str | None = None,
        switch_inline_query_current_chat: None | str | None = None,
        callback_game: CallbackGame | None = None,
        pay: bool | None = None,
        login_url: LoginUrl | None = None,
        web_app: WebAppInfo | None = None,
        switch_inline_query_chosen_chat: SwitchInlineQueryChosenChat | None = None,
        *,
        api_kwargs: JSONDict | None = None,
    ):
        """
        :param text: Button text
        :param is_selected: Initial state of the button
        :param checkbox_position: Position of the checkbox in the text
        :param checked_symbol: Symbol to use when the button is selected
        :param unchecked_symbol: Symbol to use when the button is not selected
        :param transform: Whether to transform the text and callback data
        """
        with self._unfrozen():
            self.checked_symbol = checked_symbol
            self.unchecked_symbol = unchecked_symbol
            self.checkbox_position = checkbox_position
        if transform:
            text = (
                f"{text[:checkbox_position]}"
                f"{checked_symbol if is_selected else unchecked_symbol}"
                f"{text[checkbox_position:]}"
            )
            callback_data = (
                f"{callback_data} "
                f"{self.SELECT_BTN_S} "
                f"{self.checkbox_position} "
                f"{self.checked_symbol} "
                f"{self.unchecked_symbol} "
                f"{int(is_selected)}"
            )
        super().__init__(
            text=text,
            url=url,
            callback_data=callback_data,
            switch_inline_query=switch_inline_query,
            switch_inline_query_current_chat=switch_inline_query_current_chat,
            callback_game=callback_game,
            pay=pay,
            login_url=login_url,
            web_app=web_app,
            switch_inline_query_chosen_chat=switch_inline_query_chosen_chat,
            api_kwargs=api_kwargs,
        )

    @classmethod
    def is_convertable(
        cls,
        button: Ikb,
    ) -> bool:
        """
        Returns is InlineKeyboardButton contains the appropriate callback data
        to be converted to select button.
        """
        if isinstance(button, cls):
            return False  # Already converted
        match = cls.SELECT_BTN_R.match(
            button.callback_data,
        )
        return bool(match and len(match.groups()) == cls.SELECT_BTN_R.groups)

    def invert_text(
        self,
    ) -> str:
        """Note: transforms only already transformed text."""
        if self.is_selected:
            old_symbol = self.checked_symbol
            new_symbol = self.unchecked_symbol
        else:
            old_symbol = self.unchecked_symbol
            new_symbol = self.checked_symbol
        return (
            f"{self.text[:self.checkbox_position]}"
            f"{new_symbol}"
            f"{self.text[self.checkbox_position + len(old_symbol):]}"
        )

    def invert_callback_data(self) -> str:
        """Replace last symbol which are means the flag (0 or 1)."""
        callback_data = self.callback_data
        return f"{callback_data[:-1]}{int(not self.is_selected)}"

    def invert(self) -> Self:
        """Convenient method to simply invert state of the button."""
        attrs = self.to_dict()
        attrs["text"] = self.invert_text()
        attrs["callback_data"] = self.invert_callback_data()
        attrs["is_selected"] = not self.is_selected
        return type(self)(
            transform=False,
            **attrs,
        )

    @classmethod
    def from_inline(
        cls,
        button: Ikb,
    ) -> Self:
        """
        Convert InlineKeyboardButton to SelectButton
        (callback correctness may be checked by the `is_convertable` method).
        Raises `ValueError: not enough values to unpack`
        if passed InlineKeyboardButton not contain appropriate callback data (Raise special error?)
        """
        if isinstance(button, SelectButtonBase):
            return button
        if not (
            match_result := cls.SELECT_BTN_R.match(
                button.callback_data,
            )
        ):
            raise Exceptions.NotConvertable
        _, checkbox_position, checked_symbol, unchecked_symbol, is_selected = match_result.groups()
        attrs = button.to_dict()
        return cls(
            is_selected=is_selected == "1",
            checkbox_position=int(checkbox_position),
            checked_symbol=checked_symbol,
            unchecked_symbol=unchecked_symbol,
            transform=False,
            **attrs,
        )


class SelectButton(
    SelectButtonBase,
):
    """SelectButtonBase with specified re pattern"""

    SELECT_BTN_S = "SELECT_BTN"
    SELECT_BTN_R = re.compile(
        rf".* ({SELECT_BTN_S}) (\d+) (\S+) (\S+) ([01])$",
    )


class SelectButtonManager(
    SelectButtonBase,
    ABC,
):
    """
    This class resolves to conflict of python and PTB:
    This class is kinda indicator, so should be inherited to denote,
    but PTB expects that every object has slots fields, so let's do it with slots,
    but the python don't allow multiple inheritance with slots
    without setting empty slots in every class of MRO.
    """

    __slots__ = ()
    SELECT_BTN_S: str
    SELECT_BTN_R: re.Pattern[str]

    @staticmethod
    @abstractmethod
    def resolve_is_selected(
        keyboard: Sequence[Sequence[Ikb]],
    ) -> bool:
        """
        Manager button depend on the other buttons,
        passing other buttons to init will add redundant complexity, moreover,
        manager button represents is regular select button
        (which are represents InlineKeyboardButton).
        Resolving button state is button itself  responsibility
        (because button may have custom logic),
        but detecting button state is keyboard's responsibility.
        The method accepts any type but the required type is `SelectButton` only.
        """


class SelectAllButton(
    SelectButtonManager,
):
    """Implementation of popular case of "select all" checkbox."""

    SELECT_BTN_S = "SELECT_ALL_BTN"
    SELECT_BTN_R = re.compile(
        rf".* ({SELECT_BTN_S}) (\d+) (\S+) (\S+) ([01])$",
    )

    @staticmethod
    def resolve_is_selected(
        keyboard: Sequence[Sequence[Ikb]],
    ) -> bool:
        for row in keyboard:
            for btn in row:
                if isinstance(btn, SelectButton) and btn.is_selected is not True:
                    return False
        return True

    def update(
        self,
        keyboard: Sequence[Sequence[SelectButton | Ikb]],
    ) -> Self:
        """Check self state by `resolve_is_selected` and invert if do not match."""
        if self.is_selected != self.resolve_is_selected(
            keyboard=keyboard,
        ):
            return self.invert()
        return self


class SimpleButtonBase(
    ABC,
):
    """
    Just a simple special type that tells to select keyboard
    to use his parameters of checkbox position, type, etc.
    Adding one more field in `SelectButton` isn't such a good idea IMO because
    the class itself will not use this field
    and the field data is for internal usage only, not part of the state.
    """

    __slots__ = ()
    cls: type  # Type hint


@dataclass(
    slots=True,
)
class SimpleButton(IkbStruct, SimpleButtonBase):
    """
    Implementation of SimpleButtonBase with one more `is_selected` field
    and predefined cls parameter with `SelectButton`.
    """

    is_selected: bool
    cls: type[SelectButton] = SelectButton


@dataclass(
    slots=True,
)
class SimpleButtonManager(IkbStruct, SimpleButtonBase):
    """Inheritable class for manager buttons."""

    cls: type[SelectButtonManager] = SelectAllButton


class SelectKeyboard(
    Ikm,
):
    """
    Keyboard with select buttons.
    Allows to convert InlineKeyboardButton to SelectButton
    """

    CHECKBOX_POSITION: int = 0
    CHECKED_SYMBOL: str = CHECKED_SYMBOL
    UNCHECKED_SYMBOL: str = UNCHECKED_SYMBOL

    BUTTONS = (
        SelectButton,
        SelectAllButton,
    )

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        inline_keyboard: tuple[tuple[SimpleButtonBase | SelectButtonBase | Ikb, ...], ...],
        checkbox_position: int = CHECKBOX_POSITION,
        checked_symbol: str = CHECKED_SYMBOL,
        unchecked_symbol: str = UNCHECKED_SYMBOL,
        *,
        api_kwargs: JSONDict | None = None,
    ):
        with self._unfrozen():
            self.checkbox_position = checkbox_position
            self.checked_symbol = checked_symbol
            self.unchecked_symbol = unchecked_symbol
            self.inline_keyboard = inline_keyboard
            self._convert_inline_buttons()
        super().__init__(
            inline_keyboard=self.inline_keyboard,
            api_kwargs=api_kwargs,
        )

    def _convert_inline_buttons(
        self,
    ) -> None:
        """
        Select all button not present here and should be provided separately
        (need to set up it in future updates)
        """
        inline_keyboard = [list(row) for row in self.inline_keyboard]
        for row_index, row in enumerate(inline_keyboard):
            for button_index, button in enumerate(row):
                if isinstance(button, SimpleButtonBase):
                    attrs = asdict(button)  # type: ignore[arg-type]
                    del attrs["cls"]
                    if issubclass(button.cls, SelectButtonManager):
                        inline_keyboard[row_index][button_index] = button.cls(
                            **attrs,
                            is_selected=button.cls.resolve_is_selected(  # type: ignore[union-attr]
                                keyboard=inline_keyboard,
                            ),
                        )
                    elif issubclass(button.cls, SelectButton):
                        inline_keyboard[row_index][button_index] = button.cls(
                            checkbox_position=self.checkbox_position,
                            checked_symbol=self.checked_symbol,
                            unchecked_symbol=self.unchecked_symbol,
                            **attrs,
                        )
                elif self.is_convertable(
                    button=button,
                ):
                    row[button_index] = self.button_from_inline(
                        button=button,
                    )
        self.inline_keyboard = tuple(tuple(row) for row in inline_keyboard)

    @classmethod
    def is_convertable(
        cls,
        button: Ikb,
    ) -> bool:
        """
        Sequentially checking `is_convertable` on every button from self `button_class`
        and returns first matched result.
        """
        return any(
            button_class.is_convertable(
                button=button,
            )
            for button_class in cls.BUTTONS
        )

    @classmethod
    def button_from_inline(
        cls,
        button: Ikb,
    ) -> SelectAllButton | SelectButton | None:
        """
        Sequentially checking `is_convertable` on every button from self `button_class`
        and applies `from_inline` on first matched result and returns it.
        """
        return next(
            (
                button_class.from_inline(
                    button=button,
                )
                for button_class in cls.BUTTONS
                if button_class.is_convertable(
                    button=button,
                )
            ),
            None,
        )

    @staticmethod
    def extract_select_buttons(
        inline_keyboard: Sequence[Sequence[SelectButton | Ikb]],
    ) -> list[SelectButton]:
        """
        Just get flat list of buttons of the keyboard
        P.S. Just in case, not in use currently for a class.
        """
        result = []
        for row in inline_keyboard:
            for btn in row:
                if isinstance(btn, SelectButton):
                    result.append(btn)
        return result

    @classmethod
    def is_all_buttons_selected(
        cls,
        inline_keyboard: Sequence[Sequence[SelectButton | Ikb]],
    ) -> bool:
        """
        Just in case, not in use currently for a class and responsibility of SelectAll button.
        """
        return all(
            button.is_selected
            for button in cls.extract_select_buttons(
                inline_keyboard=inline_keyboard,
            )
        )

    @staticmethod
    def find_btn(
        inline_keyboard: Sequence[Sequence[SelectButton | Ikb]],
        pattern: re.Pattern | str,
    ) -> tuple[SelectButtonBase | Ikb, int, int] | None:
        """Return button, row_index, button_index or None if not found"""
        if isinstance(pattern, str):
            pattern = re.compile(
                rf"^{re.escape(pattern)}$",
            )
        for row_index, row in enumerate(inline_keyboard):
            for button_index, button in enumerate(row):
                if pattern.match(button.callback_data):
                    return button, row_index, button_index
        return None

    @staticmethod
    def set_all_buttons(
        keyboard: Sequence[Sequence[SelectButton | Ikb]],
        flag: bool,
    ) -> list[list[SelectButton | Ikb]]:
        """
        Set all buttons flags to True of False.
        Replaces the whole button, not just updating state.
        Responsibility of SelectAll button (should accept button resolve strategy).
        """
        if not isinstance(keyboard, list):
            keyboard = [list(row) for row in keyboard]
        for row_index, buttons_row in enumerate(keyboard):
            for button_index, button in enumerate(buttons_row):
                if (
                    isinstance(
                        button,
                        SelectButton,
                    )
                    and button.is_selected != flag
                ):
                    keyboard[row_index][button_index] = button.invert()
        return keyboard

    @classmethod
    @overload
    def from_inline(
        cls,
        keyboard: Ikm,
    ) -> Self:
        pass

    @classmethod
    @overload
    def from_inline(  # type: ignore[overload-cannot-match]
        cls,
        keyboard: Sequence[Sequence[SelectButton | Ikb]],
    ) -> list[list[SelectButton | Ikb]]:
        pass

    @classmethod
    def from_inline(
        cls,
        keyboard: Ikm | Sequence[Sequence[SelectButton | Ikb]],
    ) -> Self | list[list[SelectButton | Ikb]]:
        """Converts all buttons which callback are match the select buttons callback pattern"""
        inline_keyboard = [
            list(row)
            for row in getattr(
                keyboard,
                "inline_keyboard",
                keyboard,
            )
        ]
        for row in inline_keyboard:
            for button_index, button in enumerate(row):
                if not isinstance(button, SelectButton) and cls.is_convertable(
                    button=button,
                ):
                    row[button_index] = cls.button_from_inline(
                        button=button,
                    )
        if isinstance(keyboard, Ikm):
            attrs = keyboard.to_dict()
            attrs["inline_keyboard"] = inline_keyboard
            return cls(
                **attrs,
            )
        return inline_keyboard

    @classmethod
    @overload
    def invert_by_callback(
        cls,
        cbk_data: str,
        keyboard: Ikm,
    ) -> Self: ...

    @classmethod
    @overload
    def invert_by_callback(  # type: ignore[overload-cannot-match]
        cls,
        cbk_data: str,
        keyboard: Sequence[Sequence[SelectButton | Ikb]],
    ) -> list[list[SelectButton | Ikb]]: ...

    @classmethod
    def invert_by_callback(
        cls,
        cbk_data: str,
        keyboard: Ikm | Sequence[Sequence[SelectButton | Ikb]],
    ) -> Self | list[list[SelectButton | Ikb]] | None:
        """
        param keyboard: InlineKeyboardMarkup
        param cbk_data: callback data of button
        Returns None if button is not found or is not convertable
        Indeed converting just selected button and managers button are enough
        (Replace 2 parameters on single `callback_query`?)
        """
        if isinstance(keyboard, Ikm):  # Pycharm don't understand getattr optimization
            inline_keyboard = keyboard.inline_keyboard
        else:
            inline_keyboard = keyboard
        if not (
            button_search_result := cls.find_btn(
                inline_keyboard=inline_keyboard,
                pattern=cbk_data,
            )
        ):
            return None
        inline_keyboard = cls.from_inline(
            keyboard=inline_keyboard,
        )
        _, row_index, column_index = button_search_result
        button = inline_keyboard[row_index][column_index]  # Use new value after converting
        if isinstance(button, SelectAllButton):
            inline_keyboard[row_index][column_index] = button = button.invert()
            cls.set_all_buttons(
                keyboard=inline_keyboard,
                flag=button.is_selected,
            )
        else:
            inline_keyboard[row_index][column_index] = button.invert()  # invert selected button
            all_button_search_result: tuple[SelectAllButton, int, int] | None = cls.find_btn(
                inline_keyboard=inline_keyboard,
                pattern=SelectAllButton.SELECT_BTN_R,
            )
            if all_button_search_result:
                select_all_button, row_index, column_index = all_button_search_result
                inline_keyboard[row_index][column_index] = select_all_button.update(
                    keyboard=inline_keyboard,
                )
        if isinstance(keyboard, Ikm):
            attrs = keyboard.to_dict()
            attrs["inline_keyboard"] = inline_keyboard
            return cls(
                **attrs,
            )
        return inline_keyboard
