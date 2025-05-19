import logging
from typing import Any

from django.db import DatabaseError, transaction
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from notifications.models import UserProfile

from .serializers import (
    AlertCreateSerializer,
    AlertReadOnlySerializer,
    UserProfileCreateSerializer,
)
from .tasks import fan_out_notifications

logger = logging.getLogger(__name__)


class AlertWebhookAPIView(APIView):
    """
    Receive shoplifting alerts from the external service,
    upsert into Alert, then asynchronously fan out notifications.
    """

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = AlertCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                alert = serializer.save()

        # TODO: try-catch block here could probably be done across the app as a middleware?
        except DatabaseError as db_exc:
            logger.exception(
                "DB error saving Alert",
                extra={"validated_data": serializer.validated_data},
            )
            return Response(
                {"error": "Could not persist alert"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            fan_out_notifications.delay(str(alert.alert_uuid))
        except Exception as task_exc:
            # uh-oh... celery isn't feeling well
            logger.exception(
                "Failed to enqueue notification fan-out",
                extra={"alert_uuid": str(alert.alert_uuid)},
            )
            return Response(
                {
                    "warning": "Alert saved but notifications not scheduled",
                },
                status=status.HTTP_202_ACCEPTED,
            )

        # return the up-to-date Alert representation
        read_serializer = AlertReadOnlySerializer(alert, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)


class UserProfileCreateAPIView(generics.CreateAPIView):
    """
    API endpoint to create a UserProfile for testing.
    """

    queryset = UserProfile.objects.all()
    serializer_class = UserProfileCreateSerializer
