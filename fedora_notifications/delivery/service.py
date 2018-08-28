# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""
The `Twisted`_ delivery service.

This application consumes from all the user queues and delivers notifications
via email or IRC.

.. _Twisted: https://twistedmatrix.com/
"""
from twisted.internet import reactor, endpoints, protocol, defer
from twisted.application import service, internet
from twisted.logger import Logger

from fedora_messaging.twisted.service import FedoraMessagingService

from . import irc, mail
from .. import config, db

_log = Logger()


class DeliveryService(service.MultiService):
    """
    The Twisted Service that handles the message delivery.

    This ties instances of the fedora-messaging Twisted service, which implements
    the PushProducer interface, to delivery backends. A delivery backend, such as
    IRC or email, is a Twisted service that implements the Consumer interface and
    is responsible for sending out the messages pushed to it.

    Attributes:
        irc_producer (FedoraMessagingService): An AMQP client that subscribes to
            all IRC queues and pushes them to the IRC client for delivery.
        irc_client (internet.ClientService): The Twisted IRC client service which
            is responsible for sending the messages to users. This service runs
            :class:`irc.IrcProtocol` and the :func:`irc.IrcProtocol.deliver` method
            is what is ultimately responsible for delivery.
        email_producer (FedoraMEssagingService): An AMQP client that subscribes to
            all IRC queues and pushes them to the SMTP client for delivery. When
            a message arrives it calls :func:`mail.deliver`.
    """

    name = "FedoraNotificationService"

    def __init__(self):
        service.MultiService.__init__(self)
        self.email_producer = None
        self.irc_producer = None
        self.irc_client = None

        # Although this is a blocking call, no work can happen until it's done and it's
        # a one-time call at startup.
        db.initialize(config.conf)

        irc_bindings = []
        if config.conf["IRC_ENABLED"]:
            irc_queues = db.Queue.query.filter_by(
                delivery_type=db.DeliveryType.irc, batch=None
            ).all()
            for q in irc_queues:
                irc_bindings += q.bindings()
            _log.info("Setting up and binding to {n} queues for IRC", n=len(irc_bindings))

        email_bindings = []
        if config.conf["EMAIL_ENABLED"]:
            email_queues = db.Queue.query.filter_by(
                delivery_type=db.DeliveryType.email, batch=None
            ).all()
            for q in email_queues:
                email_bindings += q.bindings()
            _log.info("Setting up and binding to {n} queues for email", n=len(email_bindings))

        db.Session.remove()

        # TODO set up a listener for messages about new queues.
        # Then we need an API to poke a message service to start a new subscription
        # or stop an existing one.
        if irc_bindings:
            self.irc_producer = FedoraMessagingService(
                self._dispatch_irc, bindings=irc_bindings
            )
            self.irc_producer.setName("irc-fedora-messaging")
            self.addService(self.irc_producer)
        if email_bindings:
            self.email_producer = FedoraMessagingService(
                mail.deliver, bindings=email_bindings
            )
            self.email_producer.setName("email-fedora-messaging")
            self.addService(self.email_producer)

        if self.irc_producer:
            irc_endpoint = endpoints.clientFromString(
                reactor, config.conf["IRC_ENDPOINT"]
            )
            irc_factory = protocol.Factory.forProtocol(irc.IrcProtocol)
            self.irc_client = internet.ClientService(irc_endpoint, irc_factory)
            self.addService(self.irc_client)

    @defer.inlineCallbacks
    def _dispatch_irc(self, message):
        """Callback for the IRC backend that waits for a connected client."""
        client = yield self.irc_client.whenConnected()
        yield client.deliver(message)

    def startService(self):
        """Called by Twisted to start the service."""
        if self.irc_client:
            self.irc_client.startService()
        if self.irc_producer:
            self.irc_producer.startService()
        if self.email_producer:
            self.email_producer.startService()

    def stopService(self):
        """Called by Twisted to stop the service."""
        if self.irc_client:
            self.irc_client.stopService()
        if self.irc_producer:
            self.irc_producer.stopService()
        if self.email_producer:
            self.email_producer.stopService()
