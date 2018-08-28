class FedoraNotificationError(Exception):
    """The base exception class."""


class ConfigurationError(FedoraNotificationError):
    """A configuration-related error."""
