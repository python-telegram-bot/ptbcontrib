#!/usr/bin/env python
"""The setup and build script for the ptbcontrib library."""

import codecs
import re
from pathlib import Path
from typing import Dict, List, Union

from setuptools import find_packages, setup

_SUB_REQ_PATTERN = re.compile(r"requirements_(\w+).txt")


def requirements(filename: Union[str, Path] = "requirements.txt") -> List[str]:
    """Build the requirements list for this project"""
    requirements_list = []

    with Path(filename).open(encoding="UTF-8") as file:
        for install in file:
            requirements_list.append(install.strip())

    return requirements_list


def requirements_extra() -> Dict[str, List[str]]:
    """Build the extra requirements list for each contribution"""
    extra_requirements: Dict[str, List[str]] = {}

    for file in Path("ptbcontrib").glob("*/requirements*.txt"):
        module = file.parent.name
        if file.name == "requirements.txt":
            extra_requirements[module] = requirements(file.absolute())
        else:
            match = _SUB_REQ_PATTERN.match(file.name)
            if match:
                extra_requirements[f"{module}_{match.group(1)}"] = requirements(file.absolute())
            else:
                extra_requirements[module] = []

    return extra_requirements


packages = find_packages(exclude=["tests*"])
reqs = requirements()
reqs_extra = requirements_extra()

with codecs.open("README.rst", "r", "utf-8") as fd:
    setup(
        name="ptbcontrib",
        author_email="devs@python-telegram-bot.org",
        license="LGPLv3",
        url="https://python-telegram-bot.org/",
        keywords="python telegram bot api wrapper contrib",
        description="Contrib package for the python-telegram-bot library",
        long_description=fd.read(),
        packages=packages,
        package_data={"ptbcontrib": ["py.typed"]},
        install_requires=reqs,
        extras_require=reqs_extra,
        include_package_data=True,
        classifiers=[
            "Development Status :: 1 - Planning",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
            "Operating System :: OS Independent",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Topic :: Communications :: Chat",
            "Topic :: Internet",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
        ],
    )
