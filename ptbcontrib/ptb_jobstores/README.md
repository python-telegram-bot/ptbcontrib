# Adapter for persisting telegram.ext.Jobs

Provides an adapter for the `SQLAlchemyJobStore` and `MongoDBJobStore` class from APScheduler package as an example, that enables persisting jobs of type `telegram.ext.Job` using standart APScheduler mechanics. Note, that this is only working on `python-telegram-bot~=20.0`, which uses `apscheduler<4.0,>=3.6.3`

## The problem

`telegram.ext.Job` instances have some unserializable fields, e.g. reference to the bot instance, so it can't be saved using standard APScheduler methods.

## The solution

The provided adapter erases all problematic fields and changes `telegram.ext.Job` instance to make it serializable. After that it passes savable `Job` instances to the APScheduler storage. When job is loaded back, the adapter recreates the job into it's original form. 

### Usage
```python
from telegram.ext import Application
from ptbcontrib.ptb_jobstores.mongodb import PTBMongoDBJobStore

DB_URI = "mongodb://botuser:botpassword@localhost:27017/admin?retryWrites=true&w=majority"

application = Application.builder().token("TOKEN").build()
application.job_queue.scheduler.add_jobstore(
    PTBMongoDBJobStore(
        application=application,
        host=DB_URI,
    )
)

application.run_polling()
```

## Note
You MUST define an explicit ID for the job and use `replace_existing=True` or you will get a new copy of the job every time your application restarts! To pass those extra arguments you can
use `job_kwargs` parameter that accepts arbitrary arguments as a dictionary and is present in all `JobQueue.run_*` methods.

For more information please have a look at APS scheduler's documentation about adding jobs by clicking [here](https://apscheduler.readthedocs.io/en/stable/userguide.html#adding-jobs).

## Requirements
Main requirement includes:

*   `python-telegram-bot[job-queue]~=20.0`

For each Python ORM, you need to install the corresponding package:

If you are using PyMongo:
*   `pymongo>=4.1,<5`

And use `requirements_mongodb.txt`.

To install this extension separately, use:

    $ pip install "ptbcontrib[ptb_jobstores_mongodb] @ git+https://github.com/python-telegram-bot/ptbcontrib.git@main"

Or, if you are using SQLAlchemy:
*   `SQLAlchemy==1.4.46`

And use `requirements_sqlalchemy.txt`.

To install this extension separately, use:

    $ pip install "ptbcontrib[ptb_jobstores_sqlalchemy] @ git+https://github.com/python-telegram-bot/ptbcontrib.git@main"
## Authors

*   [Niko Bolg](https://github.com/nkbolg)
*   [Starry Shivam](https://github.com/starry69)
*   [Holmes555](https://github.com/Holmes555)
