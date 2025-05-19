from notifications.models import ChannelChoices, Notification

from .common import NotificationBaseTestCase


class UserProfileModelTest(NotificationBaseTestCase):
    def test_should_notify_all(self):
        assert self.profile_all.should_notify(self.alert_critical)
        assert self.profile_all.should_notify(self.alert_standard)

    def test_should_notify_critical_only(self):
        assert self.profile_critical.should_notify(self.alert_critical)
        assert not self.profile_critical.should_notify(self.alert_standard)

    def test_should_notify_standard_only(self):
        assert not self.profile_standard.should_notify(self.alert_critical)
        assert self.profile_standard.should_notify(self.alert_standard)


class NotificationManagerTest(NotificationBaseTestCase):
    def test_get_or_create_pending(self):
        notification1, created1 = Notification.objects.get_or_create_pending(
            alert=self.alert_critical,
            user_profile=self.profile_all,
            channel=ChannelChoices.WEBHOOK,
        )
        # First call should create a new pending notification
        self.assertTrue(created1)
        self.assertEqual(notification1.status, Notification.StatusChoices.PENDING)

        notification2, created2 = Notification.objects.get_or_create_pending(
            alert=self.alert_critical,
            user_profile=self.profile_all,
            channel=ChannelChoices.WEBHOOK,
        )
        # Second call should not create a new one
        self.assertFalse(created2)
        self.assertEqual(notification1.pk, notification2.pk)
