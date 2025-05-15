<<<<<<< HEAD
# shared_data.py
import json
import os

file_path = "data/timetable.json"

def update_timetable(data):
    with open(file_path, "w") as f:
        json.dump(data, f)

def get_timetable():
    if not os.path.exists(file_path):
        return [["" for _ in range(6)] for _ in range(5)]
    with open(file_path, "r") as f:
        return json.load(f)
=======
# shared_data.py
import json
import os

file_path = "data/timetable.json"

def update_timetable(data):
    with open(file_path, "w") as f:
        json.dump(data, f)

def get_timetable():
    if not os.path.exists(file_path):
        return [["" for _ in range(6)] for _ in range(5)]
    with open(file_path, "r") as f:
        return json.load(f)
>>>>>>> 027277a (Initial commit)
