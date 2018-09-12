# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""
This module creates a Flask blueprint that can be registered with a Flask application.

You may find a plugin like flask_restful useful.
"""

import flask
import flask_restful

from .. import db

#: The Flask Blueprint for the v1 API.
api_blueprint = flask.Blueprint("fedora_notifications_api", __name__)


class QueueResource(flask_restful.Resource):
    """The API endpoint for Queue management."""

    def get(self):
        """
        List the user's queues.

        **Example request**:

        .. sourcecode:: http

            GET /api/v2/packages/?name=0ad&distribution=Fedora HTTP/1.1
            Accept: application/json
            Accept-Encoding: gzip, deflate
            Connection: keep-alive
            Host: localhost:5000
            User-Agent: HTTPie/0.9.4

        **Example response**:

        .. sourcecode:: http

            HTTP/1.0 200 OK
            Content-Length: 181
            Content-Type: application/json
            Date: Mon, 15 Jan 2018 20:21:44 GMT
            Server: Werkzeug/0.14.1 Python/2.7.14

            {
                "items": [
                    {
                        "distribution": "Fedora",
                        "name": "python-requests"
                        "project": "requests",
                        "ecosystem": "pypi",
                    }
                ],
                "items_per_page": 25,
                "page": 1,
                "total_items": 1
            }


        :query int page: The package page number to retrieve (defaults to 1).
        :query int items_per_page: The number of items per page (defaults to
                                   25, maximum of 250).
        :query str distribution: Filter packages by distribution.
        :query str name: The name of the package.
        :statuscode 200: If all arguments are valid. Note that even if there
                         are no projects, this will return 200.
        :statuscode 400: If one or more of the query arguments is invalid.
        """
        queues = db.Queue.query.all()
        return {
            'items': [
                {
                    "name": queue.name,
                    "type": queue.delivery_type.value,
                    "user_identity": queue.identity,
                    "batch": queue.batch,

                } for queue in queues],
            'page': 0,
            'items_per_page': 0,
            'total_items': 0,
        }

    def post(self):
        """
        Create a new queue for a user.

        **Example request**:

        .. sourcecode:: http

            POST /api/v2/packages/ HTTP/1.1
            Accept: application/json
            Accept-Encoding: gzip, deflate
            Authorization: Token gAOFi2wQPzUJFIfDkscAKjbJfXELCz0r44m57Ur2
            Connection: keep-alive
            Content-Length: 120
            Content-Type: application/json
            Host: localhost:5000
            User-Agent: HTTPie/0.9.4

            {
                "distribution": "Fedora",
                "package_name": "python-requests",
                "project_ecosystem": "pypi",
                "project_name": "requests"
            }

        .. sourcecode:: http

            HTTP/1.0 201 CREATED
            Content-Length: 69
            Content-Type: application/json
            Date: Mon, 15 Jan 2018 21:49:01 GMT
            Server: Werkzeug/0.14.1 Python/2.7.14

            {
                "distribution": "Fedora",
                "name": "python-requests"
            }


        :reqheader Authorization: API token to use for authentication
        :reqjson string distribution: The name of the distribution that contains this
            package.
        :reqjson string package_name: The name of the package in the distribution repository.
        :reqjson string project_name: The project name in Anitya.
        :reqjson string project_ecosystem: The ecosystem the project is a part of.
            If it's not part of an ecosystem, use the homepage used in the Anitya project.

        :statuscode 201: When the package was successfully created.
        :statuscode 400: When required arguments are missing or malformed.
        :statuscode 401: When your access token is missing or invalid
        :statuscode 409: When the package already exists.
        """
        pass

    def delete(self):
        """
        Delete a queue
        """
