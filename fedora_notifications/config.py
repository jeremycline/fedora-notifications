# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""
fedora-notifications can be configured with the
``/etc/fedora-notifications/config.toml`` file or by setting the
``FEDORA_NOTIFICATIONS_CONF`` environment variable to the path of the
configuration file.

fedora-notifications makes use of fedora-messaging to communicate with the AMQP
broker. It makes use of its configuration settings to do this, which has
documentation at :mod:`fedora_messaging.config`.

Each configuration option has a default value.


General Configuration
=====================

log_config
----------
A dictionary describing the logging configuration to use, in a format accepted
by :func:`logging.config.dictConfig`.

consumers_per_connection
------------------------

The number of consumers per connection to the broker. Each consumer uses a
channel, and each connection typically has a channel limit. Set this well below
the channel limit. Defaults to 1000.

.. _conf-queue-expires:

queue_expires
-------------
The amount of time in seconds a queue can exist without a consumer for it before
it is automatically removed by the broker. If batching is in use, this sets an
upper limit for the batch interval. This setting is to protect against leaking
resources with queues that aren't properly deleted, or against malicious users
with enormous batch times.

The default is 2678400 seconds (31 days).

queue_max_length
----------------
The maximum number of messages a queue can contain before messages are dropped
from the head of the queue to accommodate new messages.

The default is unlimited.

queue_max_size
--------------
The maximum number of bytes all the message bodies in a queue can consume before
messages are dropped from the head of the queue to accommodate new messages.

The default is unlimited.


.. _conf-irc:

IRC Notifications
=================

Settings related to IRC notifications.

.. _conf-irc-enabled:

irc_enabled
-----------
A boolean to control whether or not the IRC delivery method is used.

The default is ``True``.

.. _conf-irc-endpoint:

irc_endpoint
------------
The IRC server to connect to, in Twisted endpoint format. See
:func:`twisted.internet.endpoints.clientFromString` for details on the format.

The default is ``tls:chat.freenode.net:6697``

.. _conf-irc-nick:

irc_nick
--------
The nickname to use for IRC notifications.

The default is ``fedora-notif``.

.. _conf-irc-password:

irc_password
------------
The password to use when identifying to NickServ.

The default is ``None``.

.. _conf-email:

Email Notifications
===================

Settings related to email notifications.

.. _conf-email-enabled:

email_enabled
-------------
A Boolean to control whether or not the email delivery method is used.

The default is ``True``.

.. _conf-email-from-address:

email_from_address
------------------
The "From" address used in email notifications.

The default is ``notifications@localhost``.

.. _conf-smtp-server-hostname:

smtp_server_hostname
--------------------
The SMTP server's hostname.

The default is ``localhost``.

.. _conf-smtp-server-port:

smtp_server_port
----------------
The port to use when connecting to the SMTP server.

The default is 587.

.. _conf-smtp-username:

smtp_username
-------------
The username to use when authenticating with the SMTP server, if authentication
is required.

The default is ``None``.

.. _conf-smtp-password:

smtp_password
-------------
The password to use when authenticating with the SMTP server, if authentication
is required.

The default is ``None``.

.. _conf-smtp-require-authentication:

smtp_require_authentication
---------------------------
A Boolean indicating whether or not authentication is required for the SMTP server.

The default is ``False``.

.. _conf-smtp-require-tls:

smtp_require_tls
----------------
A Boolean indicating whether or not TLS is required for the SMTP server.

The default is ``False``.

.. _conf-log-config:
"""
import logging
import logging.config
import os

import pytoml

from . import exceptions


_log = logging.getLogger(__name__)

#: A dictionary of application configuration defaults.
DEFAULTS = {
    "SECRET_KEY": "change me",
    "SQL_DEBUG": False,
    "DATABASE_URL": "sqlite:////",
    "QUEUE_EXPIRES": 60 * 5,
    "QUEUE_MAX_LENGTH": None,
    "QUEUE_MAX_SIZE": None,
    "IRC_ENABLED": True,
    "IRC_ENDPOINT": "tcp:localhost:6667",
    "IRC_NICK": "fedora-notif",
    "IRC_PASSWORD": None,
    "EMAIL_ENABLED": True,
    "EMAIL_FROM_ADDRESS": "notifications@localhost",
    "SMTP_SERVER_HOSTNAME": "localhost",
    "SMTP_SERVER_PORT": 25,
    "SMTP_USERNAME": None,
    "SMTP_PASSWORD": None,
    "SMTP_REQUIRE_AUTHENTICATION": False,
    "SMTP_REQUIRE_TLS": False,
    "CONSUMERS_PER_CONNECTION": 1000,
    "LOG_CONFIG": {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"simple": {"format": "[%(name)s %(levelname)s] %(message)s"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            }
        },
        "loggers": {
            "fedora_messaging": {
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
            "fedora_notifications": {
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
            "pika": {
                "level": "WARNING",
                "propagate": False,
                "handlers": ["console"],
            },
            "alembic": {"level": "INFO", "propagate": False, "handlers": ["console"]},
            "sqlalchemy": {
                "level": "WARNING",
                "propagate": False,
                "handlers": ["console"],
            },
        },
        # The root logger configuration; this is a catch-all configuration
        # that applies to all log messages not handled by a different logger
        "root": {"level": "WARNING", "handlers": ["console"]},
    },
    "OIDC_CLIENT_SECRETS": "/etc/fedora-notifications/client_secrets.json",
}

# Start with a basic logging configuration, which will be replaced by any user-
# specified logging configuration when the configuration is loaded.
logging.config.dictConfig(DEFAULTS["LOG_CONFIG"])


class LazyConfig(dict):
    """This class lazy-loads the configuration file."""

    loaded = False

    def __getitem__(self, *args, **kw):
        if not self.loaded:
            self.load_config()
        return super(LazyConfig, self).__getitem__(*args, **kw)

    def get(self, *args, **kw):
        if not self.loaded:
            self.load_config()
        return super(LazyConfig, self).get(*args, **kw)

    def pop(self, *args, **kw):
        if not self.loaded:
            self.load_config()
        return super(LazyConfig, self).pop(*args, **kw)

    def copy(self, *args, **kw):
        if not self.loaded:
            self.load_config()
        return super(LazyConfig, self).copy(*args, **kw)

    def update(self, *args, **kw):
        if not self.loaded:
            self.load_config()
        return super(LazyConfig, self).update(*args, **kw)

    def load_config(self):
        """
        Load application configuration from a file and merge it with the default
        configuration.

        If the ``FEDORA_NOTIFICATIONS_CONF`` environment variable is set to a filesystem
        path, the configuration will be loaded from that location. Otherwise, the
        path defaults to ``/etc/fedora-notifications/config.toml``.
        """
        self.loaded = True
        config = DEFAULTS.copy()

        if "FEDORA_NOTIFICATIONS_CONF" in os.environ:
            config_path = os.environ["FEDORA_NOTIFICATIONS_CONF"]
        else:
            config_path = "/etc/fedora-notifications/config.toml"

        if os.path.exists(config_path):
            _log.info("Loading configuration from {}".format(config_path))
            with open(config_path) as fd:
                try:
                    file_config = pytoml.loads(fd.read())
                    for key in file_config:
                        config[key.upper()] = file_config[key]
                except pytoml.core.TomlError as e:
                    msg = "Failed to parse {}: error at line {}, column {}".format(
                        config_path, e.line, e.col
                    )
                    raise exceptions.ConfigurationError(msg)
        else:
            _log.info("The configuration file, {}, does not exist.".format(config_path))

        self.update(config)
        self._validate()
        logging.config.dictConfig(self["LOG_CONFIG"])
        return self

    def _validate(self):
        """Validate the configuration values."""
        if self["SECRET_KEY"] == DEFAULTS["SECRET_KEY"]:
            _log.warning(
                '"SECRET_KEY" is not configured, falling back to the default. '
                "This is NOT safe for production deployments!"
            )

        for key in ("QUEUE_EXPIRES", "QUEUE_MAX_LENGTH", "QUEUE_MAX_SIZE"):
            if self[key] and (not isinstance(self[key], int) or self[key] < 0):
                raise exceptions.ConfigurationError(
                    '"{}" must be a positive integer'.format(key)
                )


#: The application configuration dictionary.
conf = LazyConfig()
