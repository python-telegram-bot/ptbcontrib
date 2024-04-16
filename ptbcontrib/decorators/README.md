## Register a function as a handler (decorator)

```python
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes

from ptbcontrib.decorators import TelegramHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

application = ApplicationBuilder().token('TOKEN').build()

Cmd = TelegramHandler(application).command


@Cmd(command="start")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


if __name__ == '__main__':
    application.run_polling()
```


## Requirements

*   `>python-telegram-bot>=20`


