# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""The user interface views."""

import flask

from . import oidc


ui_blueprint = flask.Blueprint(
    "fedora_notifications_ui",
    __name__,
    static_folder="static",
    template_folder="templates",
)


@ui_blueprint.route("/")
def index():
    return flask.render_template("index.html")


@ui_blueprint.route("/login/")
@oidc.require_login
def login():
    """Log in using OpenID Connect."""
    flask.flash("You successfully logged in, {}".format(flask.g.user))
    return flask.redirect(flask.url_for("fedora_notifications_ui.index"))


@ui_blueprint.route("/logout/")
def logout():
    """Log out."""
    oidc.logout()
    flask.flash("You successfully logged out!")
    return flask.redirect(flask.url_for("fedora_notifications_ui.index"))
