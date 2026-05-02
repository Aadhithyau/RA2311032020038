from flask import Flask, jsonify, request
from datetime import datetime
from config import BASE_URL, ACCESS_TOKEN
import requests
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logging_middleware import Log

app = Flask(__name__)


def auth_headers():
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }


def fetch_notifications():
    response = requests.get(
        f"{BASE_URL}/notifications",
        headers=auth_headers(),
        timeout=10
    )

    if response.status_code != 200:
        return None, response.status_code

    return response.json().get("notifications", []), 200


def parse_time(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.min


def type_weight(notification_type):
    weights = {
        "Placement": 3,
        "Result": 2,
        "Event": 1
    }

    return weights.get(notification_type, 0)


def priority_score(notification):
    created_at = parse_time(notification.get("Timestamp", ""))
    timestamp_value = created_at.timestamp() if created_at != datetime.min else 0
    return (type_weight(notification.get("Type")) * 10000000000) + timestamp_value


@app.route("/", methods=["GET"])
def home():
    Log("backend", "info", "route", "Notification backend started")
    return jsonify({
        "message": "Notification backend is running"
    })


@app.route("/notifications", methods=["GET"])
def get_notifications():
    try:
        notifications, status = fetch_notifications()

        if status != 200:
            Log("backend", "error", "service", "Failed to fetch notifications")
            return jsonify({
                "error": "Unable to fetch notifications"
            }), status

        Log("backend", "info", "service", "Fetched notifications from evaluation service")

        return jsonify({
            "count": len(notifications),
            "notifications": notifications
        })

    except Exception as error:
        Log("backend", "error", "handler", str(error))
        return jsonify({
            "error": "Notification fetch failed"
        }), 500


@app.route("/notifications/priority", methods=["GET"])
def get_priority_notifications():
    try:
        n = request.args.get("n", default=10, type=int)

        if n <= 0:
            return jsonify({
                "error": "n must be greater than zero"
            }), 400

        notifications, status = fetch_notifications()

        if status != 200:
            Log("backend", "error", "service", "Failed to fetch priority notifications")
            return jsonify({
                "error": "Unable to fetch notifications"
            }), status

        ranked = sorted(
            notifications,
            key=priority_score,
            reverse=True
        )

        result = ranked[:n]

        Log("backend", "info", "controller", "Generated priority notification list")

        return jsonify({
            "requestedCount": n,
            "returnedCount": len(result),
            "priorityRule": {
                "Placement": 3,
                "Result": 2,
                "Event": 1,
                "recency": "newer notifications rank higher within same type"
            },
            "notifications": result
        })

    except Exception as error:
        Log("backend", "error", "handler", str(error))
        return jsonify({
            "error": "Priority notification calculation failed"
        }), 500


if __name__ == "__main__":
    app.run(debug=True, port=5001)