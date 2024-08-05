# Logging handler for python-telegram-bot
Extension to forward application logs to specific Telegram chats through a `logging.Handler` class.

## Usage
Initialize the log forwarder in your `on_startup` method:

```python
async def on_startup(app: Application):
    error_forwarder = LogForwarder(
        app.bot, [CHAT_ID], log_levels=["ERROR", "WARNING"]
    )
    # Add handler to the root logger to apply to all other loggers
    logging.getLogger().addHandler(error_forwarder)
```
