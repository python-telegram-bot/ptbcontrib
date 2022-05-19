.. image:: https://github.com/python-telegram-bot/logos/blob/master/ptbcontrib/png/ptbcontrib-logo-text_768.png?raw=true
   :align: center
   :target: https://github.com/python-telegram-bot/ptbcontrib
   :alt: ptbcontrib Logo

Community-based extensions for the `python-telegram-bot <https://python-telegram-bot.org>`_ library.


.. image:: https://img.shields.io/badge/python-3.6%7C3.7%7C3.8%7C3.9-blue
   :target: https://www.python.org/doc/versions/
   :alt: Supported Python versions

.. image:: https://img.shields.io/pypi/l/python-telegram-bot.svg
   :target: https://www.gnu.org/licenses/lgpl-3.0.html
   :alt: LGPLv3 License

.. image:: https://github.com/python-telegram-bot/ptbcontrib/workflows/GitHub%20Actions/badge.svg?event=push
   :target: https://github.com/python-telegram-bot/ptbcontrib/
   :alt: Github Actions workflow

.. image:: http://isitmaintained.com/badge/resolution/python-telegram-bot/ptbcontrib.svg
   :target: http://isitmaintained.com/project/python-telegram-bot/ptbcontrib
   :alt: Median time to resolve an issue

.. image:: https://app.codacy.com/project/badge/Grade/4ea8c625b01048cd94ff65bc11bd1ec0
   :target: https://www.codacy.com/gh/python-telegram-bot/ptbcontrib/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=python-telegram-bot/ptbcontrib&amp;utm_campaign=Badge_Grade
   :alt: Code quality

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/Telegram-Group-blue.svg
   :target: https://telegram.me/pythontelegrambotgroup
   :alt: Telegram Group

.. image:: https://img.shields.io/badge/IRC-Channel-blue.svg
   :target: https://webchat.freenode.net/?channels=##python-telegram-bot
   :alt: IRC Bridge

=================
Table of contents
=================

- `Introduction`_

- `Installing`_

- `Getting help`_

- `Contributing`_

- `License`_

============
Introduction
============

This library provides extensions for the `python-telegram-bot <https://python-telegram-bot.org>`_ library written and maintained by the community of PTB users.

==========
Installing
==========

Because this library is subject to more frequent changes than PTB, it is *not* available via PyPi. You can still install it via pip:

.. code:: shell

    $ pip install git+https://github.com/python-telegram-bot/ptbcontrib.git@main

If you want to use an extension that has some special requirements, you can install them on the fly as e.g.

.. code:: shell

    $ pip install "ptbcontrib[extension1,extension2] @ git+https://github.com/python-telegram-bot/ptbcontrib.git@main"

Or you can install from source with:

.. code:: shell

    $ git clone https://github.com/python-telegram-bot/ptbcontrib
    $ cd ptbcontrib
    $ python setup.py install

============
Getting help
============

You can get help in several ways:

1. We have a vibrant community of developers helping each other in our `Telegram group <https://telegram.me/pythontelegrambotgroup>`_. Join us!

2. In case you are unable to join our group due to Telegram restrictions, you can use our `IRC channel <https://webchat.freenode.net/?channels=##python-telegram-bot>`_.

3. Report bugs, request new features or ask questions by `creating an issue <https://github.com/python-telegram-bot/ptbcontrib/issues/new/choose>`_.

============
Contributing
============

Contributions of all sizes are welcome. Please review our `contribution guidelines <https://github.com/python-telegram-bot/ptbcontrib/blob/master/.github/CONTRIBUTING.rst>`_ to get started. You can also help by `reporting bugs <https://github.com/python-telegram-bot/ptbcontrib/issues/new>`_.

=======
License
=======

You may copy, distribute and modify the software provided that modifications are described and licensed for free under `LGPL-3 <https://www.gnu.org/licenses/lgpl-3.0.html>`_. Derivatives works (including modifications or anything statically linked to the library) can only be redistributed under LGPL-3, but applications that use the library don't have to be.
