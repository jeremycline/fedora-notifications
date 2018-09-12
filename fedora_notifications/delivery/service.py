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
from fedora_messaging.twisted.factory import FedoraMessagingFactory
import pika

from . import irc, mail
from .. import config, db, messages

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

    def get_queues(self, delivery_type):
        queues = db.Queue.query.filter_by(
            delivery_type=delivery_type, batch=None
        ).all()
        bindings = []
        for q in queues:
            bindings += q.bindings()
        db.Session.remove()

        return [q.arguments() for q in queues], bindings

    def __init__(self):
        service.MultiService.__init__(self)
        self.email_producer = None
        self.irc_producer = None
        self.irc_client = None

        # Map queue names to service instances
        self._queues = {}
        self._irc_queues = {}
        self._email_queues = {}
        self._irc_services = []
        self._email_services = []

        db.initialize(config.conf)

        if config.conf["IRC_ENABLED"]:
            queues, bindings = self.get_queues(db.DeliveryType.irc)
            consumers = {q["queue"]: self._dispatch_irc for q in queues}
            producer = FedoraMessagingService(
                queues=queues, bindings=bindings, consumers=consumers)
            producer.setName("irc-{}".format(len(self._irc_services)))
            self._irc_services.append(producer)
            for queue in queues:
                self._queues[queue["queue"]] = producer
            self.addService(producer)

        if config.conf["EMAIL_ENABLED"]:
            queues, bindings = self.get_queues(db.DeliveryType.email)
            consumers = {q["queue"]: mail.deliver for q in queues}
            producer = FedoraMessagingService(
                queues=queues, bindings=bindings, consumers=consumers)
            producer.setName("email-{}".format(len(self._email_services)))
            self._email_services.append(producer)
            for queue in queues:
                self._queues[queue["queue"]] = producer
            self.addService(producer)

        amqp_endpoint = endpoints.clientFromString(
            reactor, 'tcp:localhost:5672'
        )
        params = pika.URLParameters('amqp://')
        control_queue = {
            "queue": "fedora-notifications-control-queue",
            "durable": True,
        }
        factory = FedoraMessagingFactory(
            params,
            queues=[control_queue],
        )
        factory.consume(self._manage_service, control_queue["queue"])
        self.amqp_service = internet.ClientService(amqp_endpoint, factory)
        self.addService(self.amqp_service)
        # TODO set up a listener for messages about new queues.
        # Then we need an API to poke a message service to start a new subscription
        # or stop an existing one.

        if self._irc_services:
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

    def _manage_service(self, message):
        _log.info("{q}", q=str(message))
        if isinstance(message, messages.QueueCreated):
            queue_type = message.queue_name.split('.', 1)[0]
            if queue_type == "irc":
                producer = self._irc_services[0]
                producer.getFactory().consume(self._dispatch_irc, message.queue_name)
                self._queues[message.queue_name] = producer
            elif queue_type == "email":
                producer = self._email_services[0]
                producer.getFactory().consume(mail.deliver, message.queue_name)
                self._queues[message.queue_name] = producer
        elif isinstance(message, messages.QueueDeleted):
            queue_type = message.queue_name.split('.', 1)[0]
            if queue_type == "irc":
                producer = self._irc_services[0]
                producer.getFactory().cancel(message.queue_name)
                del self._queues[message.queue_name]
            elif queue_type == "email":
                producer = self._email_services[0]
                producer.getFactory().cancel(message.queue_name)
                del self._queues[message.queue_name]

    def startService(self):
        """Called by Twisted to start the service."""
        self.amqp_service.startService()
        if self.irc_client:
            self.irc_client.startService()
        for serv in self._irc_services + self._email_services:
            serv.startService()

    def stopService(self):
        """Called by Twisted to stop the service."""
        self.amqp_service.stopService()
        if self.irc_client:
            self.irc_client.stopService()
        if self.irc_producer:
            self.irc_producer.stopService()
        if self.email_producer:
            self.email_producer.stopService()
