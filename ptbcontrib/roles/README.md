# Dynamic User Access Management

Provides classes and methods for granular, hierarchical user access management. Example:

```python
from telegram import Update
from telegram.ext import Updater, TypeHandler, Filters, MessageHandler, SomeHandler
from ptbcontrib.roles import setup_roles, RolesHandler, Role

updater = Updater('TOKEN')
dp = updater.dispatcher
roles = setup_roles(dp)

roles.add_admin('authors_user_id')
roles.add_role(name='my_role_1')
my_role_1 = roles['my_role_1']
roles.add_role(name='my_role_2')
my_role_2 = roles['my_role_2']
my_role_1.add_child_role(my_role_2)

def add_to_my_role_2(update, context):
    user = update.effective_user
    context.roles['my_role_2'].add_member(user.id)
    
def add_to_my_role_1(update, context):
    user_id = int(update.message.text)
    context.roles['my_role_1'].add_member(user_id)

...

# Anyone can add themself to my_role_2
dp.add_handler(TypeHandler(Update, add_to_my_role_2))

# Only the admin can add users to my_role_1
dp.add_handler(RolesHandler(MessageHandler(Filters.message, add_to_my_role_1), roles=roles.ADMINS))

# This will be accessible by my_role_2, my_role_1 and the admin
dp.add_handler(RolesHandler(SomeHandler(...), roles=my_role_2))

# This will be accessible by my_role_1 and the admin
dp.add_handler(RolesHandler(SomeHandler(...), roles=my_role_1))

# This will be accessible by anyone except my_role_1 and my_role_2
dp.add_handler(RolesHandler(SomeHandler(...), roles=~my_role_1))

# This will be accessible only by the admins of the group the update was sent in
dp.add_handler(RolesHandler(SomeHandler(...), roles=roles.CHAT_ADMINS))

# This will be accessible only by the creator of the group the update was sent in
dp.add_handler(RolesHandler(SomeHandler(...), roles=roles.CHAT_CREATOR))

# You can compare the roles regarding hierarchy:
roles.ADMINS >=  roles['my_role_1']  # True
roles.ADMINS >=  roles['my_role_2']  # True
roles['my_role_1'] < roles['my_role_2']  # False
roles.ADMINS >= Role(...)  # False, since neither of those is a parent of the other
```

Please see the docstrings for more details.

## Requirements

*   `python-telegram-bot>=13.1`

## Authors

*   [Hinrich Mahler](https://github.com/bibo-joshi)
