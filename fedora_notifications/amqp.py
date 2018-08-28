# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
import logging

from fedora_messaging import _session, exceptions as fml_exceptions

from . import config


_log = logging.getLogger(__name__)


def create_queues_with_bindings(queues):
    """
    Create a queue synchronously with bindings.

    Args:
        queues (list): A list of queues to create. Any associated bindings will
            be created with them.
    """
    sesh = _session.PublisherSession()
    queue_args = {}
    if config.conf["queue_expires"]:
        queue_args["x-expires"] = config.conf["queue_expires"]
    if config.conf["queue_max_length"]:
        queue_args["x-max-length"] = config.conf["queue_max_lenth"]
    if config.conf["queue_max_size"]:
        queue_args["x-max-length-bytes"] = config.conf["queue_max_size"]

    for queue in queues:
        try:
            sesh.queue_declare(str(queue.id), durable=True, arguments=queue_args)
            for b in queue.topic_bindings:
                sesh.queue_bind(
                    str(queue.id), "amq.topic", routing_key=b.topic, arguments={}
                )
            for b in queue.header_bindings:
                for match in b.binding_arguments():
                    sesh.queue_bind(
                        str(queue.id), "amq.match", routing_key=None, arguments=match
                    )
        except fml_exceptions.ConnectionException as e:
            # Probably raise something that turns into a 50...2? Service unavailable
            _log.warning(
                "Failed to create the %r queue with bindings: %s", queue.id, str(e)
            )
