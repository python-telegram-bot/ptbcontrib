# Monitor your Telegram bot via chat

Provides a `PTBChatLoggingHandler` class, which is a handler for the `logging` library.
It allows to pipe application logs to a specified Telegram chat.

## Usage

### Basic example

```python
import logging
from ptbcontrib.ptb_logging_to_chat import PTBChatLoggingHandler
from telegram import Bot

logger = logging.getLogger(__name__)
bot = Bot("BOT_TOKEN")
chat_id = -123456789

logging.getLogger().addHandler(PTBChatLoggingHandler(bot, [logging.ERROR], chat_id))

logger.error("something went wrong!")
```

Result:



### Pretty example

```python
import logging
from ptbcontrib.ptb_logging_to_chat import PTBChatLoggingHandler
from telegram import Bot
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)
bot = Bot("BOT_TOKEN")
chat_id = -123456789
LOG_FORMAT = "<code>%(asctime)s - %(name)s\t- %(levelname)s\t- %(message)s</code>"

logging.getLogger().addHandler(
    PTBChatLoggingHandler(bot, [logging.ERROR], chat_id, LOG_FORMAT, parse_mode=ParseMode.HTML)
)

logger.error("something went wrong!")
```

Result:



## Requirements

## Authors

*   [alexeyqu](https://github.com/alexeyqu)
