# Extra functionality for PTB keyboards

These modules contains extended keyboard classes with extra functionality for PTB keyboards.

## Module `base keyboards`

This module provides simple base actions that mostly intended to be used as base class for other extend keyboards.
For example currently `select keyboards` made independently 
and occasionally repeats the functionality present in this base module. 

```python
class IExtendedInlineKeyboardMarkup(ABC, ):
    """ Popular keyboard actions """

    def to_list(self, ) -> list[list[InlineKeyboardButton]]:

    def find_btn_by_cbk(self, cbk: str, ) -> tuple[InlineKeyboardButton, int, int] | None:
        """ Returns buttons, row index, column index if found, None otherwise """

    def get_buttons(self, ) -> list[InlineKeyboardButton]:
        """ Just get flat list of buttons of the keyboard """

    def split(
            self,
            buttons_in_row: int,
            buttons: Sequence[InlineKeyboardButton] | None = None,
            update_self: bool = True,
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
```

Popular keyboard actions
```python


def to_list(self, ) -> list[list[InlineKeyboardButton]]:


def find_btn_by_cbk(self, cbk: str, ) -> tuple[InlineKeyboardButton, int, int] | None:
    """ Returns buttons, row index, column index if found, None otherwise """


def get_buttons(self, ) -> list[InlineKeyboardButton]:
    """ Just get flat list of buttons of the keyboard """


def split(
        self,
        buttons_in_row: int,
        buttons: Sequence[InlineKeyboardButton] | None = None,
        update_self: bool = True,
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
```

## Module `select keyboards`

This module implement checkbox buttons for PTB inline keyboard

### Class `SelectKeyboard`:

Let's first create the keyboard:

```python
SelectKeyboard(
    inline_keyboard=((InlineKeyboardButton(...))),
    checkbox_position=0, 
    checked_symbol='+', 
    unchecked_symbol='-', 
)
```

`SelectKeyboard` inherits from `InlineKeyboardMarkup`and therefore not differ from it 
and may be used as drop in replacement. 
The one more explicit meaning of keyboard is container (and therefore kind of manager or arbiter) for his buttons.

#### Use cases

You got the incoming callback with inline reply markup (buttons will be also converted if possible):
```python
select_inline_keyboard = SelectKeyboard.from_callback(keyboard=inline_keyboard_markup.inline_keyboard, )
```

Let's go even forward - and directly update the selected button in one line:
```python
select_inline_keyboard = SelectKeyboard.invert_by_callback(keyboard=inline_keyboard_markup.inline_keyboard, )
```

Or if clicked "select all" option:
```python
keyboard = SelectKeyboard.set_all_buttons(keyboard=inline_keyboard, flag=True, )
```

Check is `InlineKeyboardMarkup` can be converted to any known button type of the keyboard 
```python
button = SelectKeyboard.is_convertable(button=inline_button, )
```

Check is `InlineKeyboardMarkup` can be converted to any known button type of the keyboard 
```python
button = SelectKeyboard.button_from_inline(button=inline_button, )
```


### Class `SelectButtons:`:

```python
select_button = SelectButton(
    is_selected=True,  # is_selected: Initial state of the button
    checkbox_position=0,  # checkbox_position: Position of the checkbox in the text
    checked_symbol='+',  # checked_symbol: Symbol to use when the button is selected
    unchecked_symbol='-',  # unchecked_symbol: Symbol to use when the button is not selected
    text="Hi! I'm the button which will contain selection symbol after init",  # text: Button text
    callback_data='...',
    ...  # Other `InlineKeyboardButton` regular parameters
)
```

Class `SelectButton` represents checkbox button and provides convenience methods to manage button state. 
(note: button state is immutable according to PTB objects management policy, so most of the methods returns new state).
It's also inherits from `InlineKeyboardButton` and may be used interchangeably with it.  
After creation the button will contain callback data in format: 
`'original callback SELECT_BTN 0 + - 1'`
   
Which means:
- `'SELECT_BTN'` - key to mark button as select button.
- `'0'` - position of the select symbol in the string.
- `'+'` - symbol to apply on checking.
- `'-'` - symbol to apply on unchecking.
- `'1'` - selected state (0 - deselected).


Invert button state (text and callback_data) from `selected` to `deselected` and vice versa:
```python
inverted_button = select_button.invert()
```
Check the button state is selected:
(Note: that is the property bound to callback)
```python
select_button.is_selected  # True or False
```

#### Use cases 

Convert `InlineKeyboardButton` to `SelectButton` (To check is button convertable - use `is_convertable` method)
```python
select_button = SelectButton.from_inline_button(button=inline_keyboard_button, )
```

Is button is select button at all? - This will look up for an appropriate callback data 
which has `'SELECT_BTN'` pattern
```python
select_button = SelectButton.is_convertable(button=inline_keyboard_button, )
```

### More buttons:

#### class `SelectButtonManager`:
What if `is_selected` parameter depend on the other buttons just as for "select all" button 
which are selected when all points selected? That's what `SelectButtonManager` type mean, 
every child of it should implement `resolve_is_selected` method. 

`SelectAllButton` is child of `SelectButtonManager`
It's similar to `SelectButton` and also inherits from `InlineKeyboardButton`, 
so the button itself will decide on her state.
```python
keyboard = SelectAllButton.resolve_is_selected(keyboard=inline_keyboard, )  # True or False
```

Let's update button if `resolve_is_selected` returned opposite state:
```python
updated_select_all_button = select_all_button.update(keyboard=inline_keyboard, )  # just calling `invert` inside
```

#### class`SimpleButton:`:
Specifying the same `checked_symbol`, `unchecked_symbol`, 
etc. for every button may be tedious, so there are 2 workarounds:
1. Create common class with overriding `checked_symbol`, `unchecked_symbol`: 
`class MySelectButtton: checked_symbol = 'Ha-ha!'`
2. Use `SimpleSelectButton` - this button type will tell to keyboard to use the keyboard parameters of 
`checked_symbol`, `unchecked_symbol` rather than the button:
```python
SimpleSelectButton(is_selected=True, cls=SelectButton, ...other button fields)  
```
`SimpleSelectButton` has only two purposes: it's a delayed button creation and the indicator. 

### Common architecture notes:
1. All types may be divided on 2 parts: creation and parsing or extracting. 
`SimpleButton`, `ManagerButton` is about creation, but eventually (see point 2):
2. select button representation expressed via his callback is common or similar for all buttons:
'.* ({SELECT_BTN_S}) (\d+) (\S+) (\S+) ([01])$', so it's sing;e finish point of every button.
3. During initialization, we need a structs mostly, most methods intended to handle already initialized objects.
4. Three rings of responsibility:   
   1. Select button - target of all modifications.
   2. Button manager - strategy | logic of manipulation.
   3. Keyboard - applying and providing context to manipulate by manager on the button.
5. Term `keyboard` may mean inline keyboard (nested list) or `InlineKeyboardMarkup`, 
this depends on context and will be stick to single meaning when will be more clearing of case usage.
6. May be `SimpleButton` may be dropped and just check is select button fields filled with `None` or not
(need to make them optional in this case).


Future improvements thoughts: 
1. Create `Checkbox` class, to allow `SelectButton` able to have separate checkboxes for different states. 
2. Make more states rather than just `True` | `False`.
3. Make checkboxes of different sides (actual for 2 column keyboards), similar as point 1 but easiest as keyboard twik
4. Add Some simple set oj emojy checked | unchecked symbols.
5. Increase decoupling between keyboard and buttons, improve architecture.
6. Add `eject` method to divide between 

## Requirements

* `python-telegram-bot>=20.0`

## Authors

* [David Shiko](https://github.com/david-shiko)
