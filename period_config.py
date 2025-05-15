<<<<<<< HEAD
import json
import os

PERIOD_HEADER_PATH = "data/period_headers.json"

DEFAULT_HEADERS = [
    "8:45 - 9:35", "10:00 - 10:50", "11:15 - 12:05",
    "12:45 - 1:35", "2:00 - 2:50", "3:15 - 4:05"
]

def get_period_headers():
    if not os.path.exists(PERIOD_HEADER_PATH):
        return DEFAULT_HEADERS
    with open(PERIOD_HEADER_PATH, 'r') as f:
        return json.load(f)

def save_period_headers(headers):
    os.makedirs(os.path.dirname(PERIOD_HEADER_PATH), exist_ok=True)
    with open(PERIOD_HEADER_PATH, 'w') as f:
        json.dump(headers, f, indent=4)
=======
import json
import os

PERIOD_HEADER_PATH = "data/period_headers.json"

DEFAULT_HEADERS = [
    "8:45 - 9:35", "10:00 - 10:50", "11:15 - 12:05",
    "12:45 - 1:35", "2:00 - 2:50", "3:15 - 4:05"
]

def get_period_headers():
    if not os.path.exists(PERIOD_HEADER_PATH):
        return DEFAULT_HEADERS
    with open(PERIOD_HEADER_PATH, 'r') as f:
        return json.load(f)

def save_period_headers(headers):
    os.makedirs(os.path.dirname(PERIOD_HEADER_PATH), exist_ok=True)
    with open(PERIOD_HEADER_PATH, 'w') as f:
        json.dump(headers, f, indent=4)
>>>>>>> 027277a (Initial commit)
