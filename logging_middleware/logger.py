import os
import requests


LOG_API_URL = "http://20.207.122.201/evaluation-service/logs"


VALID_STACKS = {"backend"}

VALID_LEVELS = {"debug", "info", "warn", "error", "fatal"}

VALID_PACKAGES = {
    "cache",
    "controller",
    "cron_job",
    "db",
    "domain",
    "handler",
    "repository",
    "route",
    "service",
    "auth",
    "config",
    "middleware",
    "utils"
}


def Log(stack, level, package, message):
    token = os.getenv("ACCESS_TOKEN")

    if not token:
        return {
            "success": False,
            "error": "ACCESS_TOKEN environment variable is missing"
        }

    stack = stack.lower()
    level = level.lower()
    package = package.lower()

    if stack not in VALID_STACKS:
        return {
            "success": False,
            "error": "Invalid stack"
        }

    if level not in VALID_LEVELS:
        return {
            "success": False,
            "error": "Invalid level"
        }

    if package not in VALID_PACKAGES:
        return {
            "success": False,
            "error": "Invalid package"
        }

    payload = {
        "stack": stack,
        "level": level,
        "package": package,
        "message": message
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(LOG_API_URL, json=payload, headers=headers, timeout=5)

        return {
            "success": response.status_code in [200, 201],
            "status_code": response.status_code,
            "response": response.json()
            }

    except requests.exceptions.RequestException as error:
        return {
            "success": False,
            "error": str(error)
        }