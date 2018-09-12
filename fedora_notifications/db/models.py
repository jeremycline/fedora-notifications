# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""The database models."""
import uuid

from sqlalchemy import (
    Column,
    ForeignKey,
    UnicodeText,
    orm,
    Boolean,
    Integer,
    UniqueConstraint,
)
from fedora_messaging.api import SEVERITIES

from .meta import Base
from .types import GUID, DeliveryType
from .. import config


class User(Base):
    """
    A user of fedora-notifications.

    Attributes:
        id (uuid.uuid4): The primary key of this table.
        queues (sqlalchemy.orm.collections.InstrumentedList): A list of :class:`Queue`
            objects for this user
    """

    __tablename__ = "users"

    name = Column(UnicodeText, primary_key=True)
    queues = orm.relationship("Queue", backref="user", cascade="all, delete-orphan")

    def __repr__(self):
        return "User(name={}, queues={})".format(self.name, self.queues)


class Queue(Base):
    """
    An AMQP queue used to deliver messages to a user.

    Each queue has a delivery method associated with it (email or IRC) and one
    or more :class:`Binding` objects. The bindings are what determine which
    messages are routed into the queue.

    Attributes:
        id (uuid.uuid4): The primary key of this table.
        username (str): The foreign key to the user for which this queue exists.
        delivery_type (int): The type of delivery method. Consult the :class:`DeliveryType`
            enum for possible values. Each user can have at most one queue per
            delivery type. An example of a delivery type would be email.
        identity (str): The identity used to deliver this message. This should
            contain enough information for the delivery method to send the message.
            For example, it could be an email address or an IRC nickname.
        batch (int): The number of minutes in between batches of notifications
            from this queue. If ``None``, batching is not applied and delivery
            occurs immediately.
    """

    __tablename__ = "queues"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    username = Column(UnicodeText, ForeignKey("users.name"))
    delivery_type = Column(DeliveryType.db_type(), index=True)

    identity = Column(UnicodeText, nullable=False)
    batch = Column(Integer, nullable=True, index=True, default=None)

    topic_bindings = orm.relationship(
        "TopicBinding", backref="queue", cascade="all, delete-orphan"
    )
    header_bindings = orm.relationship(
        "HeaderBinding", backref="queue", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return "Queue(identity={}, delivery_type={}, batch={}, username={})".format(
            self.identity, self.delivery_type, self.batch, self.username)

    @property
    def name(self):
        return "{}.{}".format(self.delivery_type, self.identity)

    def bindings(self):
        """
        A list of bindings associated with this queue.

        Returns:
            list of dict: A list of dictionaries, each dictionary representing a
                binding AMQP object and suitable to be passed to fedora-messaging's
                Twisted service.
        """
        header_bindings = []
        for header in self.header_bindings:
            header_bindings += header.bindings()
        topic_bindings = [t.binding() for t in self.topic_bindings]
        return header_bindings + topic_bindings

    def arguments(self):
        """
        Arguments to create the AMQP queue.

        Returns:
            dict: A dictionary of queue creation arguments, suitable to passed to
                fedora-messaging's Twisted service.
        """
        queue_args = {}
        if config.conf["QUEUE_EXPIRES"]:
            queue_args["x-expires"] = config.conf["QUEUE_EXPIRES"] * 1000
        if config.conf["QUEUE_MAX_LENGTH"]:
            queue_args["x-max-length"] = config.conf["QUEUE_MAX_LENGTH"]
        if config.conf["QUEUE_MAX_SIZE"]:
            queue_args["x-max-length-bytes"] = config.conf["QUEUE_MAX_SIZE"]
        return {
            "queue": self.name,
            "durable": True,
            "passive": False,
            "exclusive": False,
            "auto_delete": False,
            "arguments": queue_args,
        }


class TopicBinding(Base):
    """
    An AMQP topic binding.

    Topic bindings are for advanced setups where they wish to match on the
    original published topic. If users have both topic bindings and header
    bindings, they will receive duplicates of any message that matches both.
    """

    __tablename__ = "topic_bindings"

    topic = Column(UnicodeText, nullable=False, primary_key=True)
    queue_id = Column(GUID, ForeignKey("queues.id"), primary_key=True)

    def binding(self):
        """Produce a dictionary for the fedora-messaging library."""
        return {
            "queue": self.queue.name,
            "exchange": "amq.topic",
            "routing_key": self.topic,
            "arguments": {},
        }


class HeaderBinding(Base):
    """
    An AMQP queue binding for a user's message queue.

    Each queue has one or more bindings to an exchange which determines how
    messages are routed. For details on what queues, bindings, and exchanges
    are, consult the AMQP 0.9.1 documentation.

    Messages are sorted using an AMQP header exchange. Each message has a
    ``fedora_messaging_severity`` header which is one of:

      * :data:`fedora_messaging.message.DEBUG`
      * :data:`fedora_messaging.message.INFO`
      * :data:`fedora_messaging.message.WARNING`
      * :data:`fedora_messaging.message.ERROR`

    These constants are all integers, with DEBUG < INFO < WARNING < ERROR.

    In addition to the severity header, each message has a header key for each
    package it relates to, in the format ``fedora_messaging_package_<pkg-name>``,
    and each user it relates to in the format ``fedora_messaging_user_<user-name>``.
    The value of these keys is always the Boolean value ``True``.

    A user has a queue for each delivery method (IRC and email). AMQP cannot,
    unfortunately, route based on inequalities, so in order to honor the
    severity setting, each user's queue must have a binding for a package or
    user at each of the severity level down to the lowest severity level they
    are interested in. For example, a user may have the following set of
    bindings::

      [
        {
          'fedora_messaging_package_kernel': True,
          'fedora_messaging_severity': fedora_messaging.message.WARNING,
          'x-match': 'all',
        },
        {
          'fedora_messaging_package_kernel': True,
          'fedora_messaging_severity': fedora_messaging.message.ERROR,
          'x-match': 'all',
        },
        {
          'fedora_messaging_user_bowlofeggs': True,
          'fedora_messaging_severity': fedora_messaging.message.DEBUG,
          'x-match': 'all',
        },
        {
          'fedora_messaging_user_bowlofeggs': True,
          'fedora_messaging_severity': fedora_messaging.message.INFO,
          'x-match': 'all',
        },
        {
          'fedora_messaging_user_bowlofeggs': True,
          'fedora_messaging_severity': fedora_messaging.message.WARNING,
          'x-match': 'all',
        },
        {
          'fedora_messaging_user_bowlofeggs': True,
          'fedora_messaging_severity': fedora_messaging.message.ERROR,
          'x-match': 'all',
        },
      ]

    This user would receive all messages relating to the "kernel" package that
    are WARNING or higher severity, along will *all* messages relating to the
    user "bowlofeggs".

    .. note:: The "x-match" key indicates to AMQP that both the headers
              must be present for the message to be routed to the queue.

    Attributes:
        id (uuid.uuid4): The primary key for this binding.
        severity (int): The severity of the message. For available values, consult the
            :class:`SeverityType` enum.
        key_name (str): The header key's name, for example "fedora_messaging_user_bowlofeggs".
    """

    __tablename__ = "header_bindings"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    severity = Column(Integer, nullable=False)
    key_name = Column(UnicodeText, nullable=False)
    queue_id = Column(GUID, ForeignKey("queues.id"), nullable=False)

    def bindings(self):
        binds = []
        for sev in SEVERITIES:
            if sev >= self.severity:
                binds.append(
                    {
                        "queue": self.queue.name,
                        "exchange": "amq.match",
                        "routing_key": None,
                        "arguments": {
                            "x-match": "all",
                            self.key_name: True,
                            "fedora_messaging_severity": sev,
                        },
                    }
                )
        return binds
