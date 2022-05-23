# Wrapper for the [usernameToChatAPI](https://github.com/Poolitzer/usernameToChatAPI)

This provides a wrapper for the [usernameToChatAPI](https://github.com/Poolitzer/usernameToChatAPI). The wrapper returns a `telegram.Chat` object like `telegram.Bot.get_chat` would, and takes care of the (request) logic in the background.

The API uses an userbot in the background to obtain the information for the `Chat` object. This is not possible with the plain HTTP Bot API (and that is the reason why this API exists).
```python
import asyncio

from ptbcontrib.username_to_chat_api import UsernameToChatAPI
from telegram import Bot, error

import time

bot = Bot("BOT_TOKEN")
wrapper = UsernameToChatAPI("https://localhost:1234/", "RationalGymsGripOverseas", bot)
try:
    chat = asyncio.run(wrapper.resolve("@poolitzer"))
except error.RetryAfter as e:
    time.sleep(e.retry_after)
    # both variants work
    chat = asyncio.run(wrapper.resolve("poolitzer"))
```

But there is more: This implements itself even nicer into a PTB application with a custom context 
(this uses bot_data and wrapper in there to store the wrapper, so don't override this):
```python
import logging
import asyncio

from telegram import Update, Chat
from telegram.ext import ApplicationBuilder, CallbackContext, CommandHandler, ContextTypes, Application
from ptbcontrib.username_to_chat_api import UsernameToChatAPI

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


class CustomContext(CallbackContext):
    def __init__(self, application: Application):
        super().__init__(application=application)

    @property
    def wrapper(self) -> UsernameToChatAPI:
        return self.bot_data["wrapper"]

    async def resolve_username(self, username: str) -> Chat:
        return await self.application.bot_data["wrapper"].resolve(username)


async def start(update: Update, context: CustomContext):
    chat = await context.resolve_username("PoolTalks")


if __name__ == '__main__':
    context_types = ContextTypes(context=CustomContext)
    application = ApplicationBuilder().token('TOKEN').context_types(context_types).build()
    
    wrapper = UsernameToChatAPI("https://localhost:1234/", "RationalGymsGripOverseas", application.bot)
    application.bot_data["wrapper"] = wrapper
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    application.run_polling()
    # shutting down the Username API AsyncClient. Very much optional but why not.
    asyncio.run(application.bot_data["wrapper"].shutdown())
```
## Requirements

*   `>python-telegram-bot>=20`

## Authors

*   [poolitzer](https://github.com/poolitzer)
