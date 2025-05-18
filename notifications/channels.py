import logging
from abc import abstractmethod
from typing import Any, Protocol

import httpx
from django.conf import settings

from notifications.exceptions import (
    NotificationPermanentError,
    NotificationRetryableError,
)
from notifications.serializers import OutgoingNotificationSerializer

from .models import ChannelChoices, Notification

logger = logging.getLogger(__name__)


class NotificationSendingStrategy(Protocol):
    """Abstract base class for notification sending strategies."""

    @abstractmethod
    def send(self, notification: Notification, payload: dict[str, Any]) -> bool:
        """
        Sends the notification, mutates notification.status/response_data.
        Should return None on success.
        Should raise:
          - NotificationRetryableError for transient errors (task.retry)
          - NotificationPermanentError for permanent failures (no retry)
        """


class WebhookChannelStrategy:
    """Strategy for sending notifications via a webhook."""

    def send(self, notification: Notification, payload: dict[str, Any]) -> None:
        webhook_url = getattr(
            settings,
            "NOTIFICATION_WEBHOOK_URL",
            "http://host.docker.internal:9000/webhook/notifications/",
        )
        logger.info(
            f"WebhookStrategy: Sending notification {notification.notification_uuid} to {webhook_url}"
        )
        serializer = OutgoingNotificationSerializer(data=payload)
        if not serializer.is_valid():
            msg = f"Invalid outgoing payload: {serializer.errors}"
            notification.mark_failed(msg)
            # permanent error—bad schema
            raise NotificationPermanentError(msg)

        try:
            with httpx.Client(timeout=10.0) as client:
                # response = client.post(webhook_url, json=serializer.data)
                # response.raise_for_status()
                # TODO: fake response for testing
                response = httpx.Response(status_code=200, content="OK")

        except httpx.RequestError as e:
            # network timeout / DNS failure / etc. → retry
            raise NotificationRetryableError(str(e)) from e
        except httpx.HTTPStatusError as e:
            # 4xx → permanent; 5xx → you could choose retryable
            status = e.response.status_code
            msg = f"{status}: {e.response.text[:200]}"
            if 500 <= status < 600:
                raise NotificationRetryableError(msg) from e
            else:
                raise NotificationPermanentError(msg) from e

        # success → mark and return
        notification.mark_sent(response.text)


class EmailChannelStrategy(NotificationSendingStrategy):
    """Strategy for sending notifications via email (Not Implemented)."""

    def send(self, notification: Notification, payload: dict[str, Any]) -> bool:
        logger.info(
            f"EmailStrategy: Sending notification {notification.notification_uuid} to user {notification.user.email} (Not Implemented)"
        )
        return notification.mark_pending()


class SMSChannelStrategy(NotificationSendingStrategy):
    """Strategy for sending notifications via SMS (Not Implemented)."""

    def send(self, notification: Notification, payload: dict[str, Any]) -> bool:
        logger.info(
            f"SMSStrategy: Sending notification {notification.notification_uuid} to user (Not Implemented)"
        )
        return notification.mark_pending()


CHANNEL_REGISTRY: dict[str, NotificationSendingStrategy] = {
    ChannelChoices.WEBHOOK: WebhookChannelStrategy(),
    ChannelChoices.EMAIL: EmailChannelStrategy(),
    ChannelChoices.SMS: SMSChannelStrategy(),
}


def get_channel_strategy(channel_type: str) -> NotificationSendingStrategy | None:
    """Retrieves the appropriate channel strategy from the registry."""
    return CHANNEL_REGISTRY.get(channel_type)
