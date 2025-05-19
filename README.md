# Notifications Service

Implementation of a notifications service for the Veesion technical test.
I'm not used to using Django, so I'm sure there are some things that could be done better. I tried to have a simple yet clean code structure.

## Features & Flow

1. Alert Reception

- POST /api/v1/notifications/webhooks/alerts/ accepts JSON alerts:

  ```json
  {
    "url": "https://...",
    "location": "fr-auchan-larochelle",
    "alert_uuid": "uuid-v4",
    "label": "theft",
    "time_spotted": 1742470260.083
  }
  ```

  - Idempotently upserts into the Alert model.

2. Fan‑Out

   - Celery task fan_out_notifications loads the Store’s UserProfiles, filters by critical/standard/all, and creates a pending Notification for each.

3. Dispatch

   - Bound Celery task send_notification picks up each Notification, builds the payload, invokes a channel strategy (webhook/email/SMS), and manages retries.

## Project Structure

```test
notifications/         # Main Django app
├── models.py          # Store, Alert, UserProfile, Notification
├── serializers.py     # DRF serializers for create/read and outgoing payload
├── views.py           # AlertWebhookAPIView, UserProfileCreateAPIView
├── tasks.py           # Celery tasks: fan_out_notifications, send_notification
├── channels.py        # Strategy pattern for webhook/email/SMS
├── urls.py            # API routing
├── test_*.py          # Unit & integration tests
config/                # Django & Celery configuration
├── settings.py
├── celery.py
manage.py
```

## Observability & Monitoring

- Sentry integrated for error capture (DSN via SENTRY_DSN).

- Logging: structured JSON logs planned, currently basic Python logging.

- Metrics: next steps include Prometheus instrumentation (request latency, task queue depth), Datadog tracing, and Grafana dashboards.
