# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""This module contains functions that are triggered by SQLAlchemy events."""

import logging

from sqlalchemy import event

from .meta import Session


_log = logging.getLogger(__name__)


@event.listens_for(Session, "before_flush")
def validate_settings(session, flush_context, instances):
    """
    An SQLAlchemy event listener that sets the name of a Pet if it's null and
    performs validation on the name if it's not null.

    Args:
        session (sqlalchemy.orm.session.Session): The session that is about to be committed.
        flush_context (sqlalchemy.orm.session.UOWTransaction): Unused.
        instances (object): deprecated and unused

    Raises:
        ValueError: If the settings aren't valid
    """
    pass
