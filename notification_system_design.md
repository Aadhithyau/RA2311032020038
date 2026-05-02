# Stage 1

## Core Actions

The campus notification platform should support these backend actions:

1. Create a notification
2. Fetch notifications for a student
3. Fetch unread notifications
4. Mark one notification as read
5. Mark all notifications as read
6. Delete or archive a notification
7. Send real-time notification updates

## REST API Design

### 1. Create Notification

**Endpoint**

`POST /api/notifications`

**Headers**

```json
{
  "Content-Type": "application/json",
  "Authorization": "Bearer <token>"
}
```

**Request Body**

```json
{
  "type": "Placement",
  "title": "Placement Drive",
  "message": "CSX Corporation hiring registration is open",
  "targetStudentIds": [1042, 1043, 1044],
  "priority": "high"
}
```

**Response**

```json
{
  "success": true,
  "notificationId": "9f4d23a1-4b54-4f7d-9d35-a02e2f1c83fd",
  "message": "Notification created successfully"
}
```

### 2. Fetch Notifications for Student

**Endpoint**

`GET /api/students/{studentId}/notifications?page=1&limit=20`

**Headers**

```json
{
  "Authorization": "Bearer <token>"
}
```

**Response**

```json
{
  "studentId": 1042,
  "page": 1,
  "limit": 20,
  "notifications": [
    {
      "id": "b283218f-ea5a-4b7c-93a9-1f2f240d64b0",
      "type": "Placement",
      "title": "Placement Update",
      "message": "CSX Corporation hiring",
      "isRead": false,
      "createdAt": "2026-04-22T17:51:18"
    }
  ]
}
```

### 3. Fetch Unread Notifications

**Endpoint**

`GET /api/students/{studentId}/notifications/unread`

**Headers**

```json
{
  "Authorization": "Bearer <token>"
}
```

**Response**

```json
{
  "studentId": 1042,
  "unreadCount": 2,
  "notifications": [
    {
      "id": "d146095a-0d86-4a34-9e69-3900a14576bc",
      "type": "Result",
      "message": "mid-sem",
      "isRead": false,
      "createdAt": "2026-04-22T17:51:30"
    }
  ]
}
```

### 4. Mark Notification as Read

**Endpoint**

`PATCH /api/students/{studentId}/notifications/{notificationId}/read`

**Headers**

```json
{
  "Authorization": "Bearer <token>"
}
```

**Response**

```json
{
  "success": true,
  "message": "Notification marked as read"
}
```

### 5. Mark All Notifications as Read

**Endpoint**

`PATCH /api/students/{studentId}/notifications/read-all`

**Headers**

```json
{
  "Authorization": "Bearer <token>"
}
```

**Response**

```json
{
  "success": true,
  "updatedCount": 15,
  "message": "All notifications marked as read"
}
```

### 6. Delete Notification

**Endpoint**

`DELETE /api/students/{studentId}/notifications/{notificationId}`

**Headers**

```json
{
  "Authorization": "Bearer <token>"
}
```

**Response**

```json
{
  "success": true,
  "message": "Notification deleted successfully"
}
```

## Notification Schema

```json
{
  "id": "uuid",
  "studentId": 1042,
  "type": "Placement",
  "title": "Placement Drive",
  "message": "CSX Corporation hiring registration is open",
  "isRead": false,
  "priority": "high",
  "createdAt": "2026-04-22T17:51:18",
  "readAt": null
}
```

## Real-Time Notification Mechanism

**Approach:** Server-Sent Events

**Endpoint**

`GET /api/students/{studentId}/notifications/stream`

**Headers**

```json
{
  "Authorization": "Bearer <token>"
}
```

**Event Payload**

```json
{
  "event": "notification.created",
  "data": {
    "id": "b283218f-ea5a-4b7c-93a9-1f2f240d64b0",
    "type": "Placement",
    "message": "CSX Corporation hiring",
    "createdAt": "2026-04-22T17:51:18"
  }
}
```

# Stage 2

## Database Design

The notification system needs separate tables for students, notifications, and student-wise notification status. This avoids storing repeated notification content for every student.

## Tables

### students

```sql
CREATE TABLE students (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    department VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

### notifications

```sql
CREATE TABLE notifications (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    priority VARCHAR(20) DEFAULT 'normal',
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### student_notifications

```sql
CREATE TABLE student_notifications (
    id UUID PRIMARY KEY,
    student_id INT NOT NULL,
    notification_id UUID NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (notification_id) REFERENCES notifications(id)
);
```

## Indexes

```sql
CREATE INDEX idx_student_notifications_student_id
ON student_notifications(student_id);

CREATE INDEX idx_student_notifications_unread
ON student_notifications(student_id, is_read);

CREATE INDEX idx_notifications_created_at
ON notifications(created_at);
```

## Relationships

- One student can have many notification records.
- One notification can be delivered to many students.
- `student_notifications` tracks read, unread, deleted, and delivery status for each student.

## Read/Unread Handling

When a notification is created, one row is inserted in `notifications`. For each target student, a row is inserted in `student_notifications`.

Unread notifications are fetched using:

```sql
SELECT n.id, n.type, n.title, n.message, n.created_at
FROM notifications n
JOIN student_notifications sn
ON n.id = sn.notification_id
WHERE sn.student_id = 1042
AND sn.is_read = FALSE
AND sn.is_deleted = FALSE
ORDER BY n.created_at DESC;
```

Marking a notification as read only updates the student-specific row:

```sql
UPDATE student_notifications
SET is_read = TRUE,
    read_at = CURRENT_TIMESTAMP
WHERE student_id = 1042
AND notification_id = 'notification_uuid';
```

## Scaling Notes

This design avoids duplicating notification message content. The same notification can be mapped to multiple students through `student_notifications`. Indexes on `student_id`, `is_read`, and `created_at` help fetch notification lists and unread counts faster.

# Stage 3

## Backend Flow

1. Admin or campus service sends a notification request.
2. Backend validates the request and creates one notification record.
3. Backend maps that notification to the selected students.
4. Students fetch their notifications using the student notification API.
5. Read/unread status is updated separately for each student.
6. Online students can receive new notification events through the stream endpoint.

## Components

### API Layer

Handles incoming REST requests, validates input, and returns JSON responses.

### Service Layer

Contains notification creation logic, student mapping logic, and read/unread update logic.

### Database Layer

Stores notification data and student-wise delivery/read status.

### Real-Time Layer

Uses Server-Sent Events for sending new notifications to active students.

## Failure Handling

If real-time delivery fails, the notification is still stored in the database. The student can fetch it later using the normal notification API.

# Stage 4

## Queue Based Processing

For larger notification loads, the backend should not send all notifications directly inside the request cycle. Instead, it can place notification jobs into a queue.

## Flow

1. Admin creates a notification.
2. API stores the notification.
3. A delivery job is added to a queue.
4. Worker reads the job from the queue.
5. Worker creates student notification mappings.
6. Online users receive real-time events.
7. Offline users fetch notifications later through REST APIs.

## Queue Message Format

```json
{
  "notificationId": "9f4d23a1-4b54-4f7d-9d35-a02e2f1c83fd",
  "targetStudentIds": [1042, 1043, 1044],
  "priority": "high"
}
```

## Why Queue is Useful

- API response becomes faster.
- Large student batches can be processed in the background.
- Failed jobs can be retried.
- Notification delivery becomes easier to scale.

# Stage 5

## Basic Security and Validation

The backend should protect notification APIs because only authorized users or services should create campus notifications.

## Authentication

All protected APIs should use bearer token authentication.

```json
{
  "Authorization": "Bearer <token>"
}
```

## Authorization

Notification creation should be allowed only for trusted roles such as admin, placement team, exam cell, or authorized campus services.

Students should only be allowed to read, update, or delete their own notification records.

## Input Validation

The backend should validate:

- notification type
- title
- message
- target student IDs
- priority value

Empty title or message should be rejected.

## Rate Limiting

Rate limiting can be applied to avoid repeated API abuse from the same user or service.

## Audit Logs

Important actions should be logged:

- notification created
- notification delivered
- notification read
- notification deleted
- delivery failed

# Stage 6

## Priority Inbox

The priority inbox fetches notifications from the provided Notification API and returns the top `n` notifications.

## Priority Rule

Notification priority is calculated using notification type and recency.

Type weight:

```txt
Placement = 3
Result = 2
Event = 1
```

Notifications with higher type weight are shown first. If two notifications have the same type, the newer notification is shown first.

## Endpoint Implemented

`GET /notifications/priority?n=10`

## Response

The endpoint returns the top 10 priority notifications along with the priority rule used by the backend.

## Maintaining Top 10 Efficiently

For the given API response size, sorting the fetched notifications is sufficient. If the notification volume increases continuously, the backend can maintain a small heap of size 10, so only the best 10 notifications are kept while processing new notifications.