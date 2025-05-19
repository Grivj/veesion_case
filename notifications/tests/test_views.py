import uuid

from django.urls import reverse
from rest_framework.test import APITestCase

from notifications.models import Alert, Store


class AlertWebhookAPITest(APITestCase):
    def setUp(self):
        self.url = reverse("webhook-alerts")
        Store.objects.create(location_id="store-1", name="Store 1")
        self.payload = {
            "url": "https://media.veesion.io/example.mp4",
            "location": "store-1",
            "alert_uuid": str(uuid.uuid4()),
            "label": Alert.LabelChoices.THEFT,
            "time_spotted": 1742470260.083,
        }

    def test_post_creates_alert_and_returns_200(self):
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("alert_uuid", response.data)
        self.assertTrue(
            Alert.objects.filter(alert_uuid=self.payload["alert_uuid"]).exists()
        )

    def test_idempotent_post(self):
        # POST twice with same UUID
        self.client.post(self.url, self.payload, format="json")
        response2 = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response2.status_code, 200)
        self.assertEqual(
            Alert.objects.filter(alert_uuid=self.payload["alert_uuid"]).count(), 1
        )
