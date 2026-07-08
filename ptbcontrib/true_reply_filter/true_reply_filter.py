from telegram import Message
from telegram.ext.filters import MessageFilter


class _Reply(MessageFilter):
    __slots__ = ()

    def filter(self, message: Message) -> bool:
        if not message.reply_to_message:
            return False
        if (
            message.is_topic_message
            and message.message_thread_id == message.reply_to_message.message_id
        ):
            return False
        return True


TRUE_REPLY_FILTER = _Reply(name="true_reply_filter.REPLY")
