# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
import logging

from twisted.internet import defer, error
from twisted.mail import smtp
from fedora_messaging.exceptions import Nack

from .. import config

_log = logging.getLogger(__name__)


@defer.inlineCallbacks
def deliver(message):
    """
    Send an email to the given user.

    Args:
        email_address (str): The recipient's email address.
        message (str): The formatted message, ready for dispatching.
    """
    email_address = message._queue.split('.', 1)[1]
    try:
        # TODO handle the mail server being down gracefully
        yield smtp.sendmail(
            config.conf["SMTP_SERVER_HOSTNAME"].encode('utf-8'),
            config.conf["EMAIL_FROM_ADDRESS"].encode('utf-8'),
            [email_address.encode('utf-8')],
            str(message).encode('utf-8'),
            port=config.conf["SMTP_SERVER_PORT"],
            username=config.conf["SMTP_USERNAME"],
            password=config.conf["SMTP_PASSWORD"],
            requireAuthentication=config.conf["SMTP_REQUIRE_AUTHENTICATION"],
            requireTransportSecurity=config.conf["SMTP_REQUIRE_TLS"],
        )
        _log.info("Email successfully delivered to %s", email_address)
    except error.ConnectionRefusedError as e:
        _log.error("Failed to connect to the SMTP server (%s), returning message to queue", str(e))
        raise Nack()
    except smtp.SMTPClientError as e:
        _log.info("Failed to email %s: %s", email_address, str(e))
        if e.code == 550:
            # TODO Mark email as invalid in the database
            pass
        else:
            # TODO Raise a try-again-later exception
            raise
