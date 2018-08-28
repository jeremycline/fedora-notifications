# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""Message formatters for email and IRC."""

import email as email_module

from . import config


def _base_email(email_address):
    """
    Create an email Message with some basic headers to mark the email as auto-generated.

    Args:
        email_address (str): The recipient's email address.
    Returns:
        email.Message.Message: The email message object with the 'Precedence' and 'Auto-Submitted'
            headers set.
    """
    email_message = email_module.Message.Message()
    # Although this is a non-standard header and RFC 2076 discourages it, some
    # old clients don't honour RFC 3834 and will auto-respond unless this is set.
    email_message.add_header("Precedence", "Bulk")
    # Mark this mail as auto-generated so auto-responders don't respond; see RFC 3834
    email_message.add_header("Auto-Submitted", "auto-generated")
    email_message.add_header("From", config.conf["email_from_address"])
    email_message.add_header("To", email_address)

    return email_message


def single_message_email(email_address, message):
    """
    Format a single message for an email notification.

    Args:
        email_address (str): The recipient's email address.
        message (.message.Message): A message from fedora-messaging.
    Returns:
        email.Message.Message: The email.
    """
    email = _base_email(email_address)
    email.add_header("Subject", message.summary)

    payload = str(message)
    if len(payload) >= 500000:
        # Someone has done something scary in their __str__ implementation
        payload = ("Message {} was too large to be sent!\n").format(message.id)

    email.set_payload(payload)

    return email
