# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""
This module creates a Flask blueprint that can be registered with a Flask application.

You may find a plugin like flask_restful useful.
"""

import flask

#: The Flask Blueprint for the v1 API.
api_blueprint = flask.Blueprint("fedora_notifications_api", __name__)


@api_blueprint.route("/hello")
def hello_world():
    """
    Hello world endpoint.

    **Example request**:

    .. sourcecode:: http

        GET /api/v1/hello HTTP/1.1
        Accept: application/json
        Accept-Encoding: gzip, deflate
        Connection: keep-alive
        Host: localhost:5000
        User-Agent: HTTPie/0.9.4

    **Example response**:

        HTTP/1.1 200 OK
        Content-Type: text/html; charset=utf-8
        Content-Length: 13

        Hello, world.

    :statuscode 200: The world has been properly greeted.
    :statuscode 500: I didn't handle exceptions properly and my application
                     exploded.
    """

    return "Hello, world."
