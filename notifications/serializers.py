from datetime import datetime, timezone
from typing import Any

from rest_framework import serializers

from .models import Alert, ChannelChoices, Store, UserProfile


class StoreSerializer(serializers.ModelSerializer[Store]):
    class Meta:
        model = Store
        fields = ["location_id", "name", "created", "modified"]
        read_only_fields = ["created", "modified"]


class UnixEpochDateTimeField(serializers.Field):
    """
    Accepts a float-or-int UNIX timestamp
    (seconds since epoch, e.g. 1742470260 or 1742470260.083) and returns a
    timezone-aware datetime.
    """

    def to_internal_value(self, data: Any) -> datetime:
        try:
            ts = float(data)
        except (TypeError, ValueError) as e:
            raise serializers.ValidationError(
                "Time spotted must be a UNIX timestamp (float or int)."
            ) from e
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (OSError, OverflowError) as exc:
            raise serializers.ValidationError("Invalid timestamp value.") from exc

    def to_representation(self, value: datetime) -> str:
        """return the datetime as a string in ISO-8601 format"""
        return value.isoformat()


class StoreSlugField(serializers.SlugRelatedField[Store]):
    def to_internal_value(self, data: str) -> Store:
        return Store.objects.get_or_create(location_id=data, defaults={"name": data})[0]


class AlertCreateSerializer(serializers.ModelSerializer[Alert]):
    alert_uuid = serializers.UUIDField(
        help_text="Alert UUID (will be used to update or create Alert)"
    )
    location = StoreSlugField(
        slug_field="location_id",
        queryset=Store.objects.all(),
        write_only=True,
        help_text="Store location ID (will be used to get_or_create Store)",
    )
    time_spotted = UnixEpochDateTimeField(
        write_only=True,
        help_text="Detection timestamp (UNIX float/int, e.g. 1742470260 or 1742470260.083)",
    )

    class Meta:
        model = Alert
        fields = [
            "alert_uuid",
            "url",
            "label",
            "time_spotted",
            "location",
            "created",
            "modified",
        ]
        read_only_fields = ["created", "modified"]

    def create(self, validated_data: dict[str, Any]) -> Alert:
        # TODO: also handles the creation of the store if it doesn't exist
        # TODO: not in specs, so I'm handling it here for simplicity
        # TODO: in reality, I suppose that the store is created beforehand

        return Alert.objects.update_or_create(
            alert_uuid=validated_data.pop("alert_uuid"),
            defaults={"store": validated_data.pop("location"), **validated_data},
        )[0]


class AlertReadOnlySerializer(serializers.ModelSerializer[Alert]):
    store = StoreSerializer(read_only=True)
    label = serializers.CharField(source="get_label_display", read_only=True)
    is_critical = serializers.BooleanField(read_only=True)

    class Meta:
        model = Alert
        fields = [
            "alert_uuid",
            "url",
            "store",
            "label",
            "time_spotted",
            "created",
            "is_critical",
        ]
        read_only_fields = fields


class UserProfileCreateSerializer(serializers.ModelSerializer[UserProfile]):
    user_id = serializers.UUIDField(
        help_text="External user ID, e.g. '123e4567-e89b-12d3-a456-426614174000'",
    )
    store = serializers.SlugRelatedField(
        queryset=Store.objects.all(),
        slug_field="location_id",
        help_text="Store location ID, e.g. 'fr-store-paris'",
    )
    notification_preference = serializers.ChoiceField(
        choices=UserProfile.NotificationPreferenceChoices.choices,
        help_text="User's preference for alert types",
    )
    preferred_channel = serializers.ChoiceField(
        choices=ChannelChoices.choices,
        help_text="User's preferred notification channel",
    )

    class Meta:
        model = UserProfile
        fields = [
            "user_id",
            "store",
            "notification_preference",
            "preferred_channel",
        ]


class OutgoingNotificationSerializer(serializers.Serializer[None]):
    url = serializers.URLField()
    alert_uuid = serializers.UUIDField()
    location = serializers.CharField()
    label = serializers.CharField()
    target_user_id = serializers.UUIDField()
