Case Study Lead Python
Developer
Context
You're joining Veesion, a SaaS platform as a Senior Developer. Your mission
is to design and implement a robust, scalable, and maintainable notification
system.
This system must:
Receive theft alerts via POST /webhooks/alerts/ (coming from an external
service).
Forward these alerts as notifications to another service via POST
/webhook/notifications/.
The external service sends all alerts without filtering. It does not know
user preferences.
Goals
Design the system architecture.
Ensure performance, reliability, and scalability.
Implement:
Case Study Lead Python Developer 1
The alert reception endpoint.
Notification sending following alert reception.
Functional Specifications
1. Alert Reception
Input alerts have the following format:
{
"url": "https://media.veesion.io/b36006d7-adfa-4f3c-a56c-addcb
4e4f95d.mp4",
"location": "fr-auchan-larochelle"
,
"alert_uuid": "33cbb18c-3e9d-4acc-9667-2fbe7bf29137",
"label": "theft",
"time_spotted": 1742470260.083
}
alert_uuid : unique alert identifier.
label : type of alert ( theft , suspicious , normal ).
→ theft = critical, otherwise = standard.
location : unique store identifier.
time_spotted : detection timestamp.
Alerts should be stored for long-term use.
2. User Preferences
A store (represented by the location )can have multiple users. Each alert
received as input must be sent to all users in the store according to their
configuration.
Each user can configure their profile to receive:
Only critical alerts ( label: theft )
Only standard alerts ( label: suspicious ou normal )
The two types of alerts
3. Send notifications
Notifications should be sent to the third-party service via this route:
Case Study Lead Python Developer 2
POST /webhook/notifications
Format:
{
"url": "<ALERT_URL>"
,
"alert_uuid": "<ALERT_UUID>"
,
"location": "<STORE_LOCATION>"
,
"label": "<theft | suspicious | normal>",
"target_user_id": "<TARGET_USER_ID>"
}
target_user_id : target user ID.
3. Reliability: Notifications must be delivered promptly with a delivery
guarantee.
4. Scalability: The system must be able to support a large number of
concurrent alerts/notifications.
5. Extensibility: The system must be able to easily integrate new channels
(e.g. email, SMS).
Technical instructions
Langage: Python
Framework: Django
Expected deliverables
Code source
Documentation
Estimated time to complete the test
4 hours maximum
Case Study Lead Python Developer 3