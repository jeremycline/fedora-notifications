# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
#
# vi: set ft=python :

import logging.config

from twisted.application import service

from fedora_notifications import config
from fedora_notifications.delivery.service import DeliveryService


logging.config.dictConfig(config.conf['LOG_CONFIG'])

# Configure the twisted application itself.
application = service.Application('Fedora Notification Delivery Service')
service = DeliveryService()
service.setServiceParent(application)
