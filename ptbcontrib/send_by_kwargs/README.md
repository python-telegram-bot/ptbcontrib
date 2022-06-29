# `send_by_kwargs`

Provides a function that allows to send any kind of message by just providing a dictionary of keyword arguments.

*   Tries to auto-detect the appropriate `send_*` method
*   If the call to selected `send_*` method fails, gives a helpful error message

**Note:** If `chat_id` is present in the keywords arguments but no other method fits, `send_dice` will *always* be chosen. This is due to `send_dice` currently being the only method that has solely `chat_id` as a required parameter.

Usage:

```python
from ptbcontrib.send_by_kwargs import send_by_kwargs
    
kwargs = {'text': 'Hello there', 'caption': 'General Kenobi'}

# Sends using send_message
await send_by_kwargs(bot, kwargs, chat_id=123)
    
# Sends using send_photo with a caption and ignores the text kwarg
with open('photo.jpg', 'rb') as file:
    await send_by_kwargs(bot, kwargs, photo=file, chat_id=123)
```

Please see the docstrings for more details.

## Requirements

*   `python-telegram-bot==20.0a2`

## Authors

*   [Hinrich Mahler](https://github.com/bibo-joshi)
