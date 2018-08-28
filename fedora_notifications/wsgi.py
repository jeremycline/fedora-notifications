# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""
This module creates the Flask application.

This should be used as the path for the WSGI application when configuring
the Flask development server, gunicorn, Apache, etc.
"""
from .app import create


application = create()
