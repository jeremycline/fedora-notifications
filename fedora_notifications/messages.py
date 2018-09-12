"""Internal messages sent between the Fedora Notification services."""

from fedora_messaging.message import Message


class QueueCreated(Message):
    """
    Sent to the delivery service when a new queue is created in the database.
    """
    body_schema = {
        "id": "http://fedoraproject.org/message-schema/fedora-notifications#queue-created",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent by the web front-end when a user adds a queue",
        "type": "object",
        "properties": {
            "name": {
                "description": "The name of the queue that was created",
                "type": "string",
            },
        },
        "required": ["name"],
    }
    topic = "fedora-notifications-control-queue"

    @property
    def queue_name(self):
        return self._body["name"]


class QueueDeleted(Message):
    """
    Sent to the delivery service when a queue is deleted in the database.
    """
    body_schema = {
        "id": "http://fedoraproject.org/message-schema/fedora-notifications#queue-deleted",
        "$schema": "http://json-schema.org/draft-04/schema#",
        "description": "Message sent by the web front-end when a user removes a queue",
        "type": "object",
        "properties": {
            "name": {
                "description": "The name of the queue that was deleted",
                "type": "string",
            },
        },
        "required": ["name"],
    }
    topic = "fedora-notifications-control-queue"

    @property
    def queue_name(self):
        return self._body["name"]
