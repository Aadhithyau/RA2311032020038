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

