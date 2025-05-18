import logging

from celery import Task, group, shared_task
from celery.canvas import Signature

from notifications.exceptions import (
    NotificationPermanentError,
    NotificationRetryableError,
)

from .channels import get_channel_strategy
from .models import Alert, Notification

logger = logging.getLogger(__name__)


@shared_task
def fan_out_notifications(alert_uuid: str):
    try:
        alert = Alert.objects.get(alert_uuid=alert_uuid)
    except Alert.DoesNotExist:
        logger.error(f"Alert {alert_uuid} not found.")
        return

    logger.warning(
        f"Fanning out notifications for alert {alert_uuid}",
    )
    task_signatures: list[Signature] = []
    for profile in alert.store.user_profiles.all():
        if not profile.should_notify(alert):
            continue

        notification, _ = Notification.objects.get_or_create_pending(
            alert=alert,
            user_profile=profile,
            channel=profile.preferred_channel,
        )
        task_signatures.append(send_notification.s(str(notification.notification_uuid)))

    if task_signatures:
        group(task_signatures).apply_async()


@shared_task(bind=True, max_retries=5, default_retry_delay=300)
def send_notification(self: Task, notification_uuid: str):
    logger.info(f"Send: Starting notification {notification_uuid}")
    try:
        notification = Notification.objects.select_related(
            "alert__store", "user_profile"
        ).get(notification_uuid=notification_uuid)
    except Notification.DoesNotExist:
        logger.error(f"Notification {notification_uuid} not found.")
        return

    if notification.is_sent:
        return

    # Mark this attempt
    notification.mark_attempt()

    # Build payload and choose strategy
    payload = notification.build_payload()
    strategy = get_channel_strategy(notification.channel)
    if not strategy:
        notification.mark_failed("No channel strategy")
        return

    # Attempt to send
    try:
        strategy.send(notification, payload)
    except NotificationRetryableError as exc:
        # retry up to max_retries
        raise self.retry(exc=exc) from exc
    except (NotificationPermanentError, Exception) as exc:
        # permanent failure, no need to retry
        notification.mark_failed(str(exc))
        return

    logger.info(f"Send: Completed notification {notification_uuid}")
    # ? at that point, .send() should have marked the notification as sent
