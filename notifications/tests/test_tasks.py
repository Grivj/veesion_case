import uuid

from django.test import TestCase
from django.utils import timezone

from notifications.models import Alert, ChannelChoices, Notification, Store, UserProfile
from notifications.tasks import fan_out_notifications


class FanOutNotificationsTaskTest(TestCase):
    def setUp(self):
        self.store = Store.objects.create(location_id="store-1", name="Store 1")
        self.alert = Alert.objects.create(
            alert_uuid=uuid.uuid4(),
            url="https://media.veesion.io/critical.mp4",
            store=self.store,
            label=Alert.LabelChoices.THEFT,
            time_spotted=timezone.now(),
        )
        self.profile = UserProfile.objects.create(
            user_id=uuid.uuid4(),
            store=self.store,
            notification_preference=UserProfile.NotificationPreferenceChoices.ALL,
            preferred_channel=ChannelChoices.WEBHOOK,
        )

    def test_fan_out_creates_notification(self):
        # Run fan-out synchronously (with CELERY_TASK_ALWAYS_EAGER=True)
        fan_out_notifications(str(self.alert.alert_uuid))

        notifs = Notification.objects.filter(alert=self.alert)
        # Expect exactly one notification record
        self.assertEqual(notifs.count(), 1)
        notif = notifs.first()

        # Correct linkage
        self.assertEqual(notif.user_profile, self.profile)
        self.assertEqual(notif.channel, ChannelChoices.WEBHOOK)

        # Depending on eager-mode, it may have been sent immediately,
        # so accept either PENDING or SENT.
        self.assertIn(
            notif.status,
            [Notification.StatusChoices.PENDING, Notification.StatusChoices.SENT],
        )
