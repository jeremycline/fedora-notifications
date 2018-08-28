# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""
The ``fedora-notifications`` `Click`_ management CLI.

.. _Click: http://click.pocoo.org/
"""

import os

from sqlalchemy import create_engine, pool
from alembic import config as alembic_config, command
import click

from . import config, db, exceptions


_conf_help = (
    "Path to a valid configuration file to use in place of the "
    "configuration in /etc/fedora-messaging/config.toml."
)

_alembic_help = (
    "Path to an alembic configuration file pointing to the fedora-notifications"
    " migrations."
)
_default_alembic = "/etc/fedora-notifications/alembic.ini"


@click.group()
@click.option("--conf", envvar="FEDORA_MESSAGING_CONF", help=_conf_help)
def cli(conf):
    """The fedora-notifications command line interface."""
    if conf:
        if not os.path.isfile(conf):
            raise click.exceptions.BadParameter("{} is not a file".format(conf))
        try:
            config.conf.load_config(config_path=conf)
        except exceptions.ConfigurationError as e:
            raise click.exceptions.BadParameter(str(e))


@cli.command()
@click.option("--alembic-ini", help=_alembic_help, default=_default_alembic)
def createdb(alembic_ini):
    """Create a new database."""
    connectable = create_engine(
        config.conf["DATABASE_URL"],
        echo=config.conf["SQL_DEBUG"],
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        db.Base.metadata.create_all(connection)
        command.stamp(alembic_config.Config(alembic_ini), "head")
