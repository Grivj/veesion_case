import uuid

from django.test import TestCase
from django.utils import timezone

from notifications.models import Alert, ChannelChoices, Store, UserProfile


class NotificationBaseTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.store = Store.objects.create(
            location_id="store-1",
            name="Store 1",
        )

        cls.alert_critical = Alert.objects.create(
            alert_uuid=uuid.uuid4(),
            url="https://media.veesion.io/critical.mp4",
            store=cls.store,
            label=Alert.LabelChoices.THEFT,
            time_spotted=timezone.now(),
        )
        cls.alert_standard = Alert.objects.create(
            alert_uuid=uuid.uuid4(),
            url="https://media.veesion.io/standard.mp4",
            store=cls.store,
            label=Alert.LabelChoices.SUSPICIOUS,
            time_spotted=timezone.now(),
        )

        cls.profile_all = UserProfile.objects.create(
            user_id=uuid.uuid4(),
            store=cls.store,
            notification_preference=UserProfile.NotificationPreferenceChoices.ALL,
            preferred_channel=ChannelChoices.WEBHOOK,
        )
        cls.profile_critical = UserProfile.objects.create(
            user_id=uuid.uuid4(),
            store=cls.store,
            notification_preference=UserProfile.NotificationPreferenceChoices.CRITICAL,
            preferred_channel=ChannelChoices.WEBHOOK,
        )
        cls.profile_standard = UserProfile.objects.create(
            user_id=uuid.uuid4(),
            store=cls.store,
            notification_preference=UserProfile.NotificationPreferenceChoices.STANDARD,
            preferred_channel=ChannelChoices.WEBHOOK,
        )
