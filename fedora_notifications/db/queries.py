# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""
SQLAlchemy custom Query classes.

Custom query classes are a good place to store oft-repeated queries for models.
Each model can have its own set of Query classes assigned to it. If you are
familiar with Django, this is similar to `model Managers`_.

Although it is possible to create Query objects directly, it is more common for
them to be created from session objects.

.. _model Managers:
    https://docs.djangoproject.com/en/dev/topics/db/managers/
"""
