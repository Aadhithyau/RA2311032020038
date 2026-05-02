from flask import Flask, jsonify
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

def select_tasks(vehicles, capacity):
    dp = [0] * (capacity + 1)
    chosen = [[] for _ in range(capacity + 1)]

    for vehicle in vehicles:
        task_id = vehicle.get("TaskID")
        duration = int(vehicle.get("Duration", 0))
        impact = int(vehicle.get("Impact", 0))

        if duration <= 0 or impact < 0:
            continue

        for hour in range(capacity, duration - 1, -1):
            new_score = dp[hour - duration] + impact

            if new_score > dp[hour]:
                dp[hour] = new_score
                chosen[hour] = chosen[hour - duration] + [{
                    "TaskID": task_id,
                    "Duration": duration,
                    "Impact": impact
                }]

    best_hour = max(range(capacity + 1), key=lambda h: dp[h])

    return {
        "totalDuration": best_hour,
        "totalImpact": dp[best_hour],
        "selectedTasks": chosen[best_hour]
    }


@app.route("/", methods=["GET"])
def home():
    Log("backend", "info", "route", "Vehicle maintenance scheduler started")
    return jsonify({
        "message": "Vehicle maintenance scheduler backend is running"
    })


@app.route("/depots", methods=["GET"])
def get_depots():
    try:
        response = requests.get(
            f"{BASE_URL}/depots",
            headers=auth_headers(),
            timeout=10
        )

        Log("backend", "info", "service", "Fetched depot data from evaluation service")

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as error:
        Log("backend", "error", "service", str(error))
        return jsonify({
            "error": "Unable to fetch depot data"
        }), 500
        
@app.route("/vehicles", methods=["GET"])
def get_vehicles():
    try:
        response = requests.get(
            f"{BASE_URL}/vehicles",
            headers=auth_headers(),
            timeout=10
        )

        Log("backend", "info", "service", "Fetched vehicle task data from evaluation service")

        return jsonify(response.json()), response.status_code

    except requests.exceptions.RequestException as error:
        Log("backend", "error", "service", str(error))
        return jsonify({
            "error": "Unable to fetch vehicle task data"
        }), 500
        
@app.route("/schedule", methods=["GET"])
def schedule_tasks():
    try:
        depot_response = requests.get(
            f"{BASE_URL}/depots",
            headers=auth_headers(),
            timeout=10
        )

        vehicle_response = requests.get(
            f"{BASE_URL}/vehicles",
            headers=auth_headers(),
            timeout=10
        )

        if depot_response.status_code != 200 or vehicle_response.status_code != 200:
            Log("backend", "error", "service", "Failed to fetch data for vehicle scheduling")
            return jsonify({
                "error": "Unable to fetch required scheduling data"
            }), 500

        depots = depot_response.json().get("depots", [])
        vehicles = vehicle_response.json().get("vehicles", [])

        schedules = []

        for depot in depots:
            depot_id = depot.get("ID")
            mechanic_hours = int(depot.get("MechanicHours", 0))
            result = select_tasks(vehicles, mechanic_hours)

            schedules.append({
                "depotID": depot_id,
                "mechanicHours": mechanic_hours,
                "usedHours": result["totalDuration"],
                "unusedHours": mechanic_hours - result["totalDuration"],
                "totalImpact": result["totalImpact"],
                "selectedTasks": result["selectedTasks"]
            })

        Log("backend", "info", "service", "Generated optimized maintenance schedules")

        return jsonify({
            "schedules": schedules
        })

    except Exception as error:
        Log("backend", "error", "handler", str(error))
        return jsonify({
            "error": "Scheduling failed"
        }), 500
        
@app.route("/schedule/summary", methods=["GET"])
def schedule_summary():
    try:
        depot_response = requests.get(
            f"{BASE_URL}/depots",
            headers=auth_headers(),
            timeout=10
        )

        vehicle_response = requests.get(
            f"{BASE_URL}/vehicles",
            headers=auth_headers(),
            timeout=10
        )

        if depot_response.status_code != 200 or vehicle_response.status_code != 200:
            Log("backend", "error", "service", "Failed to fetch data for schedule summary")
            return jsonify({"error": "Unable to fetch required scheduling data"}), 500

        depots = depot_response.json().get("depots", [])
        vehicles = vehicle_response.json().get("vehicles", [])

        result = []

        for depot in depots:
            mechanic_hours = int(depot.get("MechanicHours", 0))
            schedule = select_tasks(vehicles, mechanic_hours)

            result.append({
                "depotID": depot.get("ID"),
                "mechanicHours": mechanic_hours,
                "usedHours": schedule["totalDuration"],
                "unusedHours": mechanic_hours - schedule["totalDuration"],
                "totalImpact": schedule["totalImpact"],
                "selectedTaskCount": len(schedule["selectedTasks"]),
                "firstFiveSelectedTaskIDs": [
                    task["TaskID"] for task in schedule["selectedTasks"][:5]
                ]
            })

        Log("backend", "info", "controller", "Generated maintenance schedule summary")

        return jsonify({"summary": result})

    except Exception as error:
        Log("backend", "error", "handler", str(error))
        return jsonify({"error": "Schedule summary failed"}), 500


if __name__ == "__main__":
    app.run(debug=True)