# True Reply Filter

Provides a `TRUE_REPLY_FILTER` that allows you to filter only **real replies** in Telegram groups and forum topics, ignoring topic starters.

```python
from telegram.ext import MessageHandler
from ptbcontrib.true_reply_filter import TRUE_REPLY_FILTER

MessageHandler(
    TRUE_REPLY_FILTER,
    callback
)
```

## Requirements

*   `python-telegram-bot>=20.0`

## Authors

*   [Daniel](https://github.com/rozari0)
