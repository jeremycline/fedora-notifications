# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""
This package contains all the database-related code.

:mod:`.meta` contains objects required by multiple modules within this package.

:mod:`.types` contains database type definitions, such as enumerations.

:mod:`.models` contains the `SQLAlchemy`_ models that map database tables
and rows to Python objects.

:mod:`.queries` contains custom queries for the database models.

:mod:`.events` contains SQLAlchemy event handlers.

The :mod:`.migrations` package contains the `Alembic`_ database migrations.
When a new database is created, SQLAlchemy is used with the current models, and
the database is stamped with the latest Alembic migration version. From then on
changes to the database schema are managed with Alembic

.. _Alembic: http://alembic.zzzcomputing.com/en/latest/
.. _SQLAlchemy: http://www.sqlalchemy.org/
"""
from .meta import initialize, Session, Base  # noqa: F401
from .models import TopicBinding, HeaderBinding, Queue, User  # noqa: F401
from .types import DeliveryType, SeverityType  # noqa: F401
