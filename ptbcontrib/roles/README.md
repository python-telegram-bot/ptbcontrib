# Dynamic User Access Management

Provides classes and methods for granular, hierarchical user access management. Example:

```python
from telegram import Update
from telegram.ext import Updater, TypeHandler, Filters, MessageHandler, SomeHandler
from ptbcontrib.roles import setup_roles, RolesHandler, Role, BOT_DATA_KEY

updater = Updater('TOKEN')
dp = updater.dispatcher
roles = setup_roles(dp)

if 'my_role_1' not in roles:
    roles.add_role(name='my_role_1')
my_role_1 = roles['my_role_1']

if 'my_role_2' not in roles:
    roles.add_role(name='my_role_2')

roles.add_admin('authors_user_id')
my_role_2 = roles['my_role_2']
my_role_1.add_child_role(my_role_2)

def add_to_my_role_2(update, context):
    user = update.effective_user
    # 'roles' is stored in context.bot_data[BOT_DATA_KEY]
    context.roles['my_role_2'].add_member(user.id)
    
def add_to_my_role_1(update, context):
    user_id = int(update.message.text)
    context.roles['my_role_1'].add_member(user_id)

...

# Anyone can add themself to my_role_2
dp.add_handler(TypeHandler(Update, add_to_my_role_2))

# Only the admin can add users to my_role_1
dp.add_handler(RolesHandler(MessageHandler(Filters.text, add_to_my_role_1), roles=roles.admins))

# This will be accessible by my_role_2, my_role_1 and the admin
dp.add_handler(RolesHandler(SomeHandler(...), roles=my_role_2))

# This will be accessible by my_role_1 and the admin
dp.add_handler(RolesHandler(SomeHandler(...), roles=my_role_1))

# This will be accessible by anyone except my_role_1 and my_role_2
dp.add_handler(RolesHandler(SomeHandler(...), roles=~my_role_1))

# This will be accessible only by the admins of the group the update was sent in
dp.add_handler(RolesHandler(SomeHandler(...), roles=roles.chat_admins))

# This will be accessible only by the creator of the group the update was sent in
dp.add_handler(RolesHandler(SomeHandler(...), roles=roles.chat_creator))

# You can compare the roles regarding hierarchy:
roles.ADMINS >=  roles['my_role_1']  # True
roles.ADMINS >=  roles['my_role_2']  # True
roles['my_role_1'] < roles['my_role_2']  # False
roles.ADMINS >= Role(...)  # False, since neither of those is a parent of the other
```

Please see the docstrings for more details.

## Note on `ConversationHandler`

Unfortunately `RolesHandler(my_conversation_handler, roles=roles)` does *not* work. However, checking the roles for every step of the conversation is rather inefficient anyway. Instead, by applying `RolesHandler` to the `entry_points` of the `ConversationHandler`, the conversation can only be started by the selected roles and re-checking the roles within the conversation is not necessary.

## Requirements

*   `python-telegram-bot~=20.0`

## Authors

*   [Hinrich Mahler](https://github.com/bibo-joshi)
*   [GrandMoffPinky](https://github.com/grandmoffpinky)
