# Adapter for persisting telegram.ext.Jobs

Provides an adapter for the `SQLAlchemyJobStore` class from APScheduler package, that enables persisting jobs of type `telegram.ext.Job` using standart APScheduler mechanics. Note, that this is only working on `python-telegram-bot>=13.0`, which uses `apscheduler<4.0,>=3.6.3`

## The problem

`telegram.ext.Job` instances have some unserializable fields, e.g. reference to the bot instance, so it can't be saved using standard APScheduler methods.

## The solution

The provided adapter erases all problematic fields and changes `telegram.ext.Job` instance to make it serializable. After that it passes savable `Job` instances to the APScheduler storage. When job is loaded back, the adapter recreates the job into it's original form. 

### Usage
```python
from telegram.ext import Updater
from ptbcontrib.ptb_sqlalchemy_jobstore import PTBSQLAlchemyJobStore

DB_URI = "postgresql://botuser:@localhost:5432/botdb"

updater = Updater("TOKEN")
dispatcher = updater.dispatcher
dispatcher.job_queue.scheduler.add_jobstore(
   PTBSQLAlchemyJobStore(
       dispatcher=dispatcher, url=DB_URI,
    ),
)

updater.start_polling()
updater.idle()
```

## Requirements

*   `python-telegram-bot>=13.0`
*   `SQLAlchemy`

## Authors

*   [Niko Bolg](https://github.com/nkbolg)
*   [Starry Shivam](https://github.com/starry69)
