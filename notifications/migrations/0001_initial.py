# Generated by Django 5.2 on 2025-05-18 21:03

import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Store",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "location_id",
                    models.CharField(
                        help_text="Unique store identifier, e.g., fr-auchan-larochelle",
                        max_length=255,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Optional descriptive name for the store",
                        max_length=255,
                    ),
                ),
            ],
            options={
                "verbose_name": "Store",
                "verbose_name_plural": "Stores",
                "ordering": ["-created"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Alert",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "alert_uuid",
                    models.UUIDField(
                        editable=False,
                        help_text="Unique alert identifier from the external service",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "url",
                    models.URLField(help_text="URL of the alert media", max_length=500),
                ),
                (
                    "label",
                    models.CharField(
                        choices=[
                            ("theft", "Theft"),
                            ("suspicious", "Suspicious"),
                            ("normal", "Normal"),
                        ],
                        help_text="Type of alert (theft, suspicious, normal)",
                        max_length=20,
                    ),
                ),
                (
                    "time_spotted",
                    models.DateTimeField(
                        help_text="Timestamp of when the alert was detected by the source"
                    ),
                ),
                (
                    "store",
                    models.ForeignKey(
                        help_text="The store where the alert originated",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alerts",
                        to="notifications.store",
                        verbose_name="Store",
                    ),
                ),
            ],
            options={
                "verbose_name": "Alert",
                "verbose_name_plural": "Alerts",
                "ordering": ["-time_spotted"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UserProfile",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "user_id",
                    models.UUIDField(
                        help_text="Opaque ID of the user in the external system"
                    ),
                ),
                (
                    "notification_preference",
                    models.CharField(
                        choices=[
                            ("critical", "Critical alerts only"),
                            ("standard", "Standard alerts only"),
                            ("all", "All alerts"),
                        ],
                        default="all",
                        help_text="User's preference for receiving alert notifications",
                        max_length=20,
                    ),
                ),
                (
                    "preferred_channel",
                    models.CharField(
                        choices=[
                            ("webhook", "Webhook"),
                            ("email", "Email"),
                            ("sms", "SMS"),
                        ],
                        default="webhook",
                        help_text="User's preferred channel for receiving notifications (e.g., webhook, email)",
                        max_length=20,
                    ),
                ),
                (
                    "store",
                    models.ForeignKey(
                        help_text="The store this user profile is associated with",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="user_profiles",
                        to="notifications.store",
                        verbose_name="Store",
                    ),
                ),
            ],
            options={
                "verbose_name": "User Profile",
                "verbose_name_plural": "User Profiles",
                "ordering": ["-created"],
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Notification",
            fields=[
                (
                    "created",
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="created",
                    ),
                ),
                (
                    "modified",
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="modified",
                    ),
                ),
                (
                    "notification_uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        verbose_name="Notification UUID",
                    ),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[
                            ("webhook", "Webhook"),
                            ("email", "Email"),
                            ("sms", "SMS"),
                        ],
                        default="webhook",
                        max_length=20,
                        verbose_name="Channel",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("sent", "Sent"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="Status",
                    ),
                ),
                (
                    "last_attempt_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Last Attempt At"
                    ),
                ),
                (
                    "attempt_count",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Attempt Count"
                    ),
                ),
                (
                    "response_data",
                    models.TextField(
                        blank=True, null=True, verbose_name="Response Data"
                    ),
                ),
                (
                    "alert",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="notifications.alert",
                        verbose_name="Alert",
                    ),
                ),
                (
                    "user_profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="notifications.userprofile",
                        verbose_name="User Profile",
                    ),
                ),
            ],
            options={
                "verbose_name": "Notification",
                "verbose_name_plural": "Notifications",
                "ordering": ["-created"],
            },
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(
                fields=["store", "time_spotted"], name="notificatio_store_i_6a5b3a_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="alert",
            index=models.Index(fields=["label"], name="notificatio_label_45f1a6_idx"),
        ),
        migrations.AddIndex(
            model_name="userprofile",
            index=models.Index(
                fields=["user_id", "store"], name="notificatio_user_id_b358fe_idx"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="userprofile",
            unique_together={("user_id", "store")},
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["alert", "user_profile", "channel"],
                name="notificatio_alert_i_8e5f43_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["status", "last_attempt_at"],
                name="notificatio_status_a636d7_idx",
            ),
        ),
    ]
