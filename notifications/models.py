import uuid
from datetime import datetime, timezone
from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from model_utils.models import TimeStampedModel

User = get_user_model()


class Store(TimeStampedModel):
    location_id = models.CharField(
        max_length=255,
        unique=True,
        primary_key=True,
        help_text=_("Unique store identifier, e.g., fr-auchan-larochelle"),
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text=_("Optional descriptive name for the store"),
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = _("Store")
        verbose_name_plural = _("Stores")
        ordering = ["-created"]

    def __str__(self) -> str:
        return self.location_id


class Alert(TimeStampedModel):
    class LabelChoices(models.TextChoices):
        THEFT = "theft", _("Theft")
        SUSPICIOUS = "suspicious", _("Suspicious")
        NORMAL = "normal", _("Normal")

    alert_uuid = models.UUIDField(
        primary_key=True,
        editable=False,
        help_text=_("Unique alert identifier from the external service"),
    )
    url = models.URLField(max_length=500, help_text=_("URL of the alert media"))
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="alerts",
        verbose_name=_("Store"),
        help_text=_("The store where the alert originated"),
    )
    label = models.CharField(
        max_length=20,
        choices=LabelChoices.choices,
        help_text=_("Type of alert (theft, suspicious, normal)"),
    )
    time_spotted = models.DateTimeField(
        help_text=_("Timestamp of when the alert was detected by the source")
    )

    class Meta(TimeStampedModel.Meta):
        verbose_name = _("Alert")
        verbose_name_plural = _("Alerts")
        indexes = [
            # fetch alerts in a given timeframe...
            models.Index(fields=["store", "time_spotted"]),
            models.Index(fields=["label"]),
        ]
        ordering = ["-time_spotted"]

    def __str__(self) -> str:
        created_time_str = self.created.strftime("%Y-%m-%d %H:%M")
        time_spotted_str = self.time_spotted.strftime("%Y-%m-%d %H:%M")
        return (
            f"{self.get_label_display()} alert ({self.alert_uuid}) at {self.store} "
            f"spotted on {time_spotted_str}, received on {created_time_str}"
        )

    @property
    def is_critical(self) -> bool:
        return self.label == self.LabelChoices.THEFT


class ChannelChoices(models.TextChoices):
    WEBHOOK = "webhook", _("Webhook")
    EMAIL = "email", _("Email")  # TODO: Not implemented
    SMS = "sms", _("SMS")  # TODO: Not implemented


class UserProfile(TimeStampedModel):
    class NotificationPreferenceChoices(models.TextChoices):
        CRITICAL = "critical", _("Critical alerts only")  # label: theft
        STANDARD = "standard", _("Standard alerts only")  # label: suspicious or normal
        ALL = "all", _("All alerts")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.UUIDField(help_text="Opaque ID of the user in the external system")

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,  # TODO: zombie profile for now on store deletion, might wanna soft delete
        related_name="user_profiles",
        verbose_name=_("Store"),
        help_text=_("The store this user profile is associated with"),
    )
    notification_preference = models.CharField(
        max_length=20,
        choices=NotificationPreferenceChoices.choices,
        default=NotificationPreferenceChoices.ALL,
        help_text=_("User's preference for receiving alert notifications"),
    )
    preferred_channel = models.CharField(
        max_length=20,
        choices=ChannelChoices.choices,
        default=ChannelChoices.WEBHOOK,
        help_text=_(
            "User's preferred channel for receiving notifications (e.g., webhook, email)"
        ),
    )

    def should_notify(self, alert: Alert) -> bool:
        pref = self.notification_preference
        match pref:
            case self.NotificationPreferenceChoices.ALL:
                return True
            case self.NotificationPreferenceChoices.CRITICAL:
                return alert.is_critical
            case self.NotificationPreferenceChoices.STANDARD:
                return not alert.is_critical
            case _:
                raise ValueError(f"Invalid notification preference: {pref}")

    class Meta(TimeStampedModel.Meta):
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
        # one user profile per store
        unique_together = [["user_id", "store"]]
        indexes = [models.Index(fields=["user_id", "store"])]
        ordering = ["-created"]

    def __str__(self) -> str:
        return f"Profile for {self.user_id} in store {self.store.location_id if self.store else 'N/A'}"


class NotificationManager(models.Manager["Notification"]):
    def get_or_create_pending(
        self, alert: Alert, user_profile: UserProfile, channel: str
    ):
        return self.update_or_create(
            alert=alert,
            user_profile=user_profile,
            channel=channel,
            defaults={
                "status": self.model.StatusChoices.PENDING,
                "last_attempt_at": None,
                "attempt_count": 0,
                "response_data": None,
            },
        )


class Notification(TimeStampedModel):

    class StatusChoices(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        FAILED = "failed", _("Failed")

    notification_uuid = models.UUIDField(
        _("Notification UUID"), primary_key=True, default=uuid.uuid4, editable=False
    )
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Alert"),
    )
    user_profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("User Profile"),
    )
    channel = models.CharField(
        _("Channel"),
        max_length=20,
        choices=ChannelChoices.choices,
        default=ChannelChoices.WEBHOOK,
    )
    status = models.CharField(
        _("Status"),
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDING,
    )
    last_attempt_at = models.DateTimeField(_("Last Attempt At"), null=True, blank=True)
    attempt_count = models.PositiveIntegerField(_("Attempt Count"), default=0)
    response_data = models.TextField(_("Response Data"), blank=True, null=True)

    objects = NotificationManager()

    @property
    def is_sent(self) -> bool:
        return self.status == self.StatusChoices.SENT

    def mark_attempt(self):
        self.attempt_count = F("attempt_count") + 1
        self.last_attempt_at = datetime.now(timezone.utc)
        self.status = self.StatusChoices.PENDING
        self.save(update_fields=["attempt_count", "last_attempt_at", "status"])

    def mark_sent(self, response_data: str):
        self.status = self.StatusChoices.SENT
        self.response_data = response_data
        self.save(update_fields=["status", "response_data"])
        return True

    def mark_failed(self, response_data: str):
        self.status = self.StatusChoices.FAILED
        self.response_data = response_data
        self.save(update_fields=["status", "response_data"])
        return False

    def mark_pending(self):
        self.status = self.StatusChoices.PENDING
        self.save(update_fields=["status"])
        return True

    def build_payload(self) -> dict[str, Any]:
        return {
            "url": self.alert.url,
            "alert_uuid": str(self.alert.alert_uuid),
            "location": self.alert.store.location_id,
            "label": self.alert.label,
            "target_user_id": str(self.user_profile.user_id),
        }

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=["alert", "user_profile", "channel"]),
            models.Index(fields=["status", "last_attempt_at"]),
        ]

    def __str__(self) -> str:
        return (
            f"Notification {self.notification_uuid} for alert {self.alert.alert_uuid} "
            f"to user {self.user_profile.user_id} via {self.get_channel_display()} "
            f"({self.get_status_display()})"
        )
