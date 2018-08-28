"""Internal messages sent between the Fedora Notification services."""

from fedora_messaging import Message


class QueueCreated(Message):
    """
    Sent to the delivery service when a new queue is created in the database.
    """


class QueueDeleted(Message):
    """
    Sent to the delivery service when a queue is deleted in the database.
    """
