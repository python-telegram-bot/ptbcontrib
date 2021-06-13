# Adapter for persisting telegram.ext.Jobs

Provides adapter for `SQLAlchemyJobStore` class from apscheduler package, that enables persisting jobs of type `telegram.ext.Job` using standart apscheduler's mechanics. Note, that this is only working in python-telegram-bot>=13.0.

## The problem

`telegram.ext.Job` instances have some unserializable fields, like, for example, reference to the bot instance, so it can't be saved using standart apscheduler's methods.

## The solution

Provided adapter erases all problematic fields and changes `telegram.ext.Job` instance to make it serializable. After that he passes savable Job to the apscheduler's storage. When job is loaded back, adapter recreates the job into it's original form. 

## Requirements

*   `python-telegram-bot>=13.0`

## Authors

*   [Niko Bolg](https://github.com/nkbolg)
*   [Starry Shivam](https://github.com/starry69)
