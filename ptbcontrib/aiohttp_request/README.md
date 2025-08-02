# AiohttpRequest instance

This is an implementation of [`BaseRequest`](docs.ptb.org/…) based on [aiohttp](https://aiohttp-docs), to be used as alternative for [`HTTPXRequest`](docs.ptb.org/…)  based on the request in [#4560](python-telegram-bot/python-telegram-bot#4560).

This can be used either in a bot instance like this:
```python
import asyncio
import telegram
from ptbcontrib.aiohttp_request import AiohttpRequest


async def main():
    bot = telegram.Bot("TOKEN", request=AiohttpRequest(), get_updates_request=AiohttpRequest())
    async with bot:
        print(await bot.get_me())


if __name__ == '__main__':
    asyncio.run(main())
```

or in an application instance like this:
```python
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from ptbcontrib.aiohttp_request import AiohttpRequest

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

if __name__ == '__main__':
    application = ApplicationBuilder().request(AiohttpRequest(connection_pool_size=256)).get_updates_request(AiohttpRequest()).token('TOKEN').build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    application.run_polling()
```

Read the class documentation for more parameters and what they do.