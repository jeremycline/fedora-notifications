# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""The Twisted IRC client for notification delivery."""
import logging

from twisted.words.protocols import irc

from .. import config

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class IrcProtocol(irc.IRCClient):
    """
    A sub-class of the IRC protocol implementation in Twisted that handles
    events and sends messages.

    Attributes:
        lineRate (float): The number of seconds of delay between lines sent
            to the IRC server, useful to avoid throttling.
        sourceURL (str): Response used in the CTCP SOURCE request.
    """

    def __init__(self, *args, **kwargs):
        self.lineRate = 0.6
        self.sourceURL = "http://github.com/fedora-infra/fedora-notifications"
        self.realname = "Fedora Notification Service"
        self.nickname = config.conf["IRC_NICK"]
        self.commands = {}

    def signedOn(self):
        """
        Called when the client has successfully connected to the IRC server.

        Note that at this point the client is not authenticated with NickServ.
        """
        log.info("Signed on to %s as %r.", self.hostname, self.nickname)
        if config.conf["IRC_PASSWORD"]:
            log.info("Identifying with NickServ as %s", self.nickname)
            self.msg(
                "NickServ",
                "IDENTIFY {nick} {password}".format(
                    nick=config.conf["IRC_NICK"], password=config.conf["IRC_PASSWORD"]
                ),
            )

    def deliver(self, message):
        """
        Deliver a message to a user or channel.

        Args:
            identity (str): The user or channel to send the message to.
            message (str): The formatted message ready for delivery.
        """
        user = message._queue.split('.', 1)[1]
        return self.msg(user, message.summary)

    def privmsg(self, user, channel, msg):
        """Called when a user sends a private message to the client."""
        log.info("Received private message from %s", user)
        if user == "NickServ!NickServ@services.":
            self._handle_nickserv_messages(msg)
        else:
            nick = user.split("!")[0]
            command = msg.split(None, 1)[0].lower()
            try:
                self.commands[command](nick, msg)
            except KeyError:
                self._default_privmsg_response(nick, msg)

    def _default_privmsg_response(self, nick, message):
        return self.msg(nick, "I didn't understand that")

    def _handle_nickserv_messages(message):
        """
        Process responses from NickServ that are a result of queries we've sent.

        Args:
            message (str): The message sent to the client by NickServ
        """
        nick, commands, result = message.split(None, 2)

        if result.strip() == "3":
            # TODO mark the user's identity as valid in DB (done in a thread)
            pass
        else:
            # TODO Provide useful feedback to the user.
            pass
