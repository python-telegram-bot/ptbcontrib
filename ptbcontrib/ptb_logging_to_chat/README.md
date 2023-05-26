# Monitor your Telegram bot via chat

Provides a `PTBChatLoggingHandler` class, which is a handler for the `logging` library.
It allows to pipe application logs to a specified Telegram chat via the Telegram API.

## Usage

### Basic example

```python
import logging
from ptbcontrib.ptb_logging_to_chat import PTBChatLoggingHandler

logger = logging.getLogger(__name__)
chat_id = -123456789

logger.addHandler(PTBChatLoggingHandler("BOT_TOKEN", [logging.ERROR], chat_id))

logger.error("something went wrong!")
```

Result:



### Pretty example

```python
import logging
from ptbcontrib.ptb_logging_to_chat import PTBChatLoggingHandler
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)
chat_id = -123456789
LOG_FORMAT = "<code>%(asctime)s - %(name)s\t- %(levelname)s\t- %(message)s</code>"

logger.addHandler(
    PTBChatLoggingHandler("BOT_TOKEN", [logging.ERROR], chat_id, LOG_FORMAT, parse_mode=ParseMode.HTML)
)

logger.error("something went wrong!")
```

Result:

### Note

Bear in mind that most Python packages log a lot of debug information.
Therefore it is not recommended to use `PTBChatLoggingHandler` for the root logger (a.k.a. `logging.getLogger()`) with the `logging.DEBUG` level.

```python
# this is a bad idea
logging.getLogger().addHandler(PTBChatLoggingHandler("BOT_TOKEN", [logging.DEBUG], chat_id))
```

## Authors

*   [alexeyqu](https://github.com/alexeyqu)