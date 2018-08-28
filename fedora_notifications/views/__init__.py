# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""This package contains Flask blueprints."""
from flask_oidc import OpenIDConnect

#: The OpenID Connect object used for authentication. The application initializes
#: this object in :func:`fedora_notifications.app.create`, but it needs to exist
#: in order for the views to use its decorators.
oidc = OpenIDConnect()
