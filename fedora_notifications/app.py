# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""Functions related to building the Flask application."""

import flask
import flask_restful
import sqlalchemy

from . import db, config, __version__
from .views import api, ui, oidc


def create(config_obj=None):
    """
    Create an instance of the Flask application.

    Args:
        config_obj (object): A module or object with configuration options
            attached to it. See the `Flask configuration documentation`_ for
            usage details.

    Returns:
        flask.Flask: The configured Flask application.

    .. _Flask configuration documentation:
        http://flask.pocoo.org/docs/latest/api/#flask.Config.from_object
    """
    app = flask.Flask(__name__)
    if config_obj:
        app.config.from_object(config_obj)
    else:
        app.config.update(config.conf.load_config())
    db.initialize(app.config)
    oidc.init_app(app)

    app.before_request(pre_request_user)
    app.teardown_request(post_request_database)
    app.context_processor(include_template_variables)

    app.api = flask_restful.Api(app)
    app.api.add_resource(api.QueueResource, "/api/v1/queues/")
    app.register_blueprint(ui.ui_blueprint)
    return app


def pre_request_user():
    """Set up the user as a flask global object."""
    if oidc.user_loggedin:
        email = oidc.user_getfield("email")
        if email:
            try:
                user = db.User.query.filter_by(name=email).one()
            except sqlalchemy.orm.exc.NoResultFound:
                user = db.User(name=email)
                db.Session.add(user)
                db.Session.commit()
            flask.g.user = user
            return
    flask.g.user = None


def post_request_database(*args, **kwargs):
    """
    Release database resources allocated during this request.

    Flask provides an error to this callback if there was one, but this is
    unused and any uncommitted transaction is rolled back here.
    """
    db.Session.remove()


def include_template_variables():
    """Include variables for the HTML templates to use during rendering."""
    return {"app_version": __version__, "user_logged_in": oidc.user_loggedin}
