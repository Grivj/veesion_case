class NotificationRetryableError(Exception):
    """Raised by a strategy when the error is transient
    and the task should be retried."""


class NotificationPermanentError(Exception):
    """Raised by a strategy when the error is permanent
    and the task should NOT be retried."""
