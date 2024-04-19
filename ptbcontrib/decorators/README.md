## An optional way of decorating a callback handler


### What is NewCommandHandler & NewCommandHandler
 - It allows to some extras features over `PTB`.
 - `telegram.ext.CommandHandler` direct not allow to use `prefix` but with `NewCommandHandler` we can use `prefix`.
 - By Default `telegram.ext.CommandHandler` or `telegram.ext.MessageHandler` get updates after edit a message but in Decorator we can set `allow_edit` as we want .
 - Other all behaviour same as `telegram.ext.CommandHandler` or `telegram.ext.MessageHandler`


### Methods :
```python
from telegram.ext import ApplicationBuilder
from ptbcontrib.decorators import TelegramHandler

application = ApplicationBuilder().token('TOKEN').build()

# For CommandHandler
Cmd = TelegramHandler(application).command
# For CallbackQueryHandler
Cb = TelegramHandler(application).callback_query
# For ChatMemberHandler
ChatMember = TelegramHandler(application).chat_member
#For InlineQueryHandler
Inline = TelegramHandler(application).inline_query

```
### Example :
```python
import logging

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, filters

from ptbcontrib.decorators import TelegramHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

application = ApplicationBuilder().token('TOKEN').build()

Cmd = TelegramHandler(application).command
Msg = TelegramHandler(application).message


@Cmd(command=["start", "help"])
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")


@Msg(filters=filters.ChatType.PRIVATE & ~filters.COMMAND)
async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)

if __name__ == '__main__':
    application.run_polling()

```


### Requirements

*   `>python-telegram-bot>=20`


