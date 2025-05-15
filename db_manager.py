import json
import os
import csv

DB_PATH = "data/student_db.json"
TIMETABLE_PATH = "data/timetable.json"
ATTENDANCE_LOG_PATH = "data/attendance_logs.csv"

# Load the student database
def load_students():
    if not os.path.exists(DB_PATH):
        return {}
    with open(DB_PATH, 'r') as f:
        return json.load(f)

# Save the student database
def save_students(students):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # Ensure directory exists
    with open(DB_PATH, 'w') as f:
        json.dump(students, f, indent=4)

# Register a new student
def register_student(student_info):
    students = load_students()
    email = student_info['email']
    if email in students:
        return False  # Student already exists

    # Store essential student details (exclude sensitive information)
    student_data = {
        'first_name': student_info['first_name'],
        'last_name': student_info['last_name'],
        'email': student_info['email'],
        'phone': student_info['phone'],
        'degree': student_info['degree'],  # Added degree to student info
        'courses': student_info['courses'],  # Added courses to student info
    }
    students[email] = student_data
    save_students(students)
    return True

# Authenticate a student
def authenticate_student(email, password):
    students = load_students()
    # For security, password checking is skipped for this example.
    return email in students

# Load the timetable
def load_timetable():
    if not os.path.exists(TIMETABLE_PATH):
        return [["" for _ in range(6)] for _ in range(5)]
    with open(TIMETABLE_PATH, 'r') as f:
        return json.load(f)

# Save the timetable
def save_timetable(timetable):
    os.makedirs(os.path.dirname(TIMETABLE_PATH), exist_ok=True)  # Ensure directory exists
    with open(TIMETABLE_PATH, 'w') as f:
        json.dump(timetable, f, indent=4)

# Mark attendance for a student
def mark_attendance(email, row, col):
    students = load_students()
    student = students.get(email)
    if not student:
        return False

    name = f"{student['first_name']} {student['last_name']}"
    reg_no = student.get('reg_no', 'NA')  # Default to 'NA' if no reg_no is set
    period = f"{['Monday','Tuesday','Wednesday','Thursday','Friday'][row]} - Period {col+1}"

    os.makedirs("data", exist_ok=True)  # Ensure 'data' directory exists
    with open(ATTENDANCE_LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([name, reg_no, period, "Present"])
    return True

# Get the first name of a student
def get_first_name(email):
    students = load_students()
    student = students.get(email)
    return student['first_name'] if student else None

# Get the last name of a student
def get_last_name(email):
    students = load_students()
    student = students.get(email)
    return student['last_name'] if student else None

# Optionally, add functions to get degree and courses (if needed for other uses)
def get_degree(email):
    students = load_students()
    student = students.get(email)
    return student['degree'] if student else None

def get_courses(email):
    students = load_students()
    student = students.get(email)
    return student['courses'] if student else None
