# Apply Filters to `update.effective_message.reply_to_message`

Provides a class `ReplyToMessageFilter` that allows you to apply Filters to `update.effective_message.reply_to_message`.

```python
from telegram.ext import Filters, MessageHandler
from ptbcontrib.reply_to_message_filter import ReplyToMessageFilter
    
# accepts only messages that are replies to text messages
replies_to_text = MessageHandler(
    ReplyToMessageFilter(Filters.text),
    callback
)
    
# accepts only messages that are replies to non-sticker messages
replies_to_anything_but_stickers = MessageHandler(
    ~ReplyToMessageFilter(Filters.sticker),
    callback
)
    
# accepts only messages containing documents that are replies to
# a message containing a document
documents_as_reply_to_documents = MessageHandler(
    Filters.document & ReplyToMessageFilter(Filters.document),
    callback
)
```

## Requirements

*   `python-telegram-bot==20.0a2`

## Authors

*   [Hinrich Mahler](https://github.com/bibo-joshi)
