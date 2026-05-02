import os

BASE_URL = "http://20.207.122.201/evaluation-service"


def load_token():
    env_path = os.path.join(os.path.dirname(__file__), ".env")

    if not os.path.exists(env_path):
        return None

    with open(env_path, "r") as file:
        for line in file:
            if line.startswith("ACCESS_TOKEN="):
                return line.strip().split("=", 1)[1]

    return None


ACCESS_TOKEN = load_token()