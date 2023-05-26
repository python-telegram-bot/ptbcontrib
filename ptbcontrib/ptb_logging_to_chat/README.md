# Monitor your Telegram bot via chat

Provides a `PTBChatLoggingHandler` class, which is a handler for the `logging` library. <br>
It allows to pipe application logs to a specified Telegram chat via the Telegram API.

Under the hood it leverages [the Telegram API sendMessage endpoint](https://core.telegram.org/method/messages.sendMessage), calling it via the `requests.post` method.

## Usage

### Basic example

```python
import logging
from ptbcontrib.ptb_logging_to_chat import PTBChatLoggingHandler

logger = logging.getLogger(__name__)
chat_id = -123456789

logging.getLogger().addHandler(PTBChatLoggingHandler("BOT_TOKEN", [logging.ERROR], chat_id))

logger.error("something went wrong!")
```

Result:

![image](https://github.com/alexeyqu/ptbcontrib/assets/7394728/fae832a4-072d-4756-9525-eb97886b205c)


### Pretty example

```python
import logging
from ptbcontrib.ptb_logging_to_chat import PTBChatLoggingHandler
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)
chat_id = -123456789
LOG_FORMAT = "<code>%(asctime)s - %(name)s\t- %(levelname)s\t- %(message)s</code>"

logging.getLogger().addHandler(
    PTBChatLoggingHandler("BOT_TOKEN", [logging.ERROR], chat_id, LOG_FORMAT, parse_mode=ParseMode.HTML)
)

logger.error("something went wrong!")
```

Result:

![image](https://github.com/alexeyqu/ptbcontrib/assets/7394728/59ca52bf-277a-4a4a-a8cb-5567fafc72e0)


### Note

Bear in mind that most Python packages log a lot of debug information.
Therefore it is not recommended to use `PTBChatLoggingHandler` for the root logger (a.k.a. `logging.getLogger()`) with the `logging.DEBUG` level.

```python
# this is a bad idea
logging.getLogger().addHandler(PTBChatLoggingHandler("BOT_TOKEN", [logging.DEBUG], chat_id))
```

You can get more information about logger hierarchy from [the logging library docs](https://docs.python.org/3/library/logging.html#logger-objects).

## Authors

*   [alexeyqu](https://github.com/alexeyqu)
