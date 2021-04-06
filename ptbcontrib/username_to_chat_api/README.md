# Wrapper for the [usernameToChatAPI](https://github.com/Poolitzer/usernameToChatAPI)

This provides a wrapper for the [usernameToChatAPI](https://github.com/Poolitzer/usernameToChatAPI). The wrapper returns a `telegram.Chat` object like `telegram.Bot.get_chat` would, and takes care of the (request) logic in the background.

The API uses an userbot in the background to obtain the information for the `Chat` object. This is not possible with the plain HTTP Bot API (and that is the reason why this API exists).
```python
from ptbcontrib.username_to_chat_api import UsernameToChatAPI
from telegram import Bot, error

import time

bot = Bot("BOT_TOKEN")
# or you could get it from updater.bot
wrapper = UsernameToChatAPI("https://localhost:1234/", "RationalGymsGripOverseas", bot)
# this could be saved to bot_data, but should only be initiated once
try:
    chat = wrapper.resolve("@poolitzer")
except error.RetryAfter as e:
    time.sleep(e.retry_after)
    # both variants work
    chat = wrapper.resolve("poolitzer")


```

## Requirements

*   `python-telegram-bot>=13.0`

## Authors

*   [poolitzer](https://github.com/poolitzer)
