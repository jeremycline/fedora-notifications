#!/usr/bin/env python

import os

from setuptools import setup, find_packages
import re


def get_project_version():
    """Read the declared version of the project from the source code"""
    version_file = "fedora_notifications/__init__.py"
    with open(version_file, "rb") as f:
        version_pattern = b'^__version__ = "(.+)"$'
        match = re.search(version_pattern, f.read(), re.MULTILINE)
    if match is None:
        err_msg = "No line matching  %r found in %r"
        raise ValueError(err_msg % (version_pattern, version_file))
    return match.groups()[0].decode("utf-8")


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst")) as fd:
    README = fd.read()


def get_requirements(requirements_file="requirements.txt"):
    """Get the contents of a file listing the requirements.

    Args:
        requirements_file (str): The path to the requirements file, relative
                                 to this file.

    Returns:
        list: the list of requirements, or an empty list if
              ``requirements_file`` could not be opened or read.
    """
    with open(requirements_file) as fd:
        lines = fd.readlines()
    dependencies = []
    for line in lines:
        maybe_dep = line.strip()
        if maybe_dep.startswith("#"):
            # Skip pure comment lines
            continue
        if maybe_dep.startswith("git+"):
            # VCS reference for dev purposes, expect a trailing comment
            # with the normal requirement
            __, __, maybe_dep = maybe_dep.rpartition("#")
        else:
            # Ignore any trailing comment
            maybe_dep, __, __ = maybe_dep.partition("#")
        # Remove any whitespace and assume non-empty results are dependencies
        maybe_dep = maybe_dep.strip()
        if maybe_dep:
            dependencies.append(maybe_dep)
    return dependencies


setup(
    name="fedora_notifications",
    version=get_project_version(),
    description="IRC and email notifications generated from AMQP messages.",
    long_description=README,
    url="https://github.com/fedora-infra/fedora-notifications",
    # Possible options are at https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    license="GPLv2+",
    maintainer="Fedora Infrastructure Team",
    maintainer_email="infrastructure@lists.fedoraproject.org",
    platforms=["Fedora", "GNU/Linux"],
    keywords="fedora",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=get_requirements(),
    tests_require=get_requirements(requirements_file="dev-requirements.txt"),
    test_suite="fedora_notifications.tests",
    entry_points={
        "console_scripts": ["fedora-notifications=fedora_notifications.cli:cli"]
    },
)
