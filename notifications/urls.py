from django.urls import path

from .views import AlertWebhookAPIView, UserProfileCreateAPIView

urlpatterns = [
    path("webhooks/alerts/", AlertWebhookAPIView.as_view(), name="webhook-alerts"),
    path("profiles/", UserProfileCreateAPIView.as_view(), name="profile-create"),
]
