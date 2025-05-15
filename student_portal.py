import sys
import threading
import socket
import cv2
import numpy as np
import pyaudio
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QTableWidget, QTableWidgetItem, QHBoxLayout,
    QMessageBox, QDesktopWidget, QComboBox, QScrollArea, QCheckBox
)
from PyQt5.QtGui import QImage, QPixmap, QColor
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal

import db_manager
import period_config
import facultyclass
import face_logic
from fullscreen_window import FullscreenWindow

import phone_pixel_detection


class ParticipationMonitor(QThread):
    alert = pyqtSignal(str)

    def __init__(self, email, interval=30):
        super().__init__()
        self.email = email
        self.interval = interval
        self._running = True

    def run(self):
        while self._running:
            time.sleep(self.interval)
            detected = face_logic.verify_face(self.email)
            if not detected:
                self.alert.emit("Face not detected! Please stay active on screen.")

    def stop(self):
        self._running = False


class StudentPortal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Portal")
        self.resize(900, 600)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.init_login_ui()

        self.video_socket = None
        self.audio_socket = None
        self.audio_stream = None
        self.running = False

        self.participation_monitor = None

    def init_login_ui(self):
        self.clear_layout()

        self.login_label = QLabel("Student Login")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.authenticate)

        self.register_btn = QPushButton("Register")
        self.register_btn.clicked.connect(self.init_register_ui)

        self.layout.addWidget(self.login_label)
        self.layout.addWidget(self.email_input)
        self.layout.addWidget(self.password_input)
        self.layout.addWidget(self.login_btn)
        self.layout.addWidget(self.register_btn)

    def init_register_ui(self):
        self.clear_layout()

        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("First Name")

        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("Last Name")

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Phone Number")

        self.degree_combo = QComboBox()
        self.degree_combo.addItem("Select Degree")
        self.degree_combo.addItems(["B.Tech", "EEE", "ECE"])

        self.course_label = QLabel("Select Course(s):")
        self.course_scroll_area = QScrollArea()
        self.course_scroll_area.setWidgetResizable(True)

        self.course_widget = QWidget()
        self.course_layout = QVBoxLayout()
        self.courses = [
            "Core Computer Science",
            "CSE Specialization (Big Data Analytics)",
            "Cyber Security",
            "CSE Specialization (Internet of Things - IoT)",
            "CSE Specialization (Cloud Computing)"
        ]

        self.course_checkboxes = []
        for course in self.courses:
            checkbox = QCheckBox(course)
            self.course_checkboxes.append(checkbox)
            self.course_layout.addWidget(checkbox)

        self.course_widget.setLayout(self.course_layout)
        self.course_scroll_area.setWidget(self.course_widget)

        self.capture_btn = QPushButton("Capture Face")
        self.capture_btn.clicked.connect(self.capture_face)

        self.submit_btn = QPushButton("Submit Registration")
        self.submit_btn.clicked.connect(self.submit_registration)

        self.back_btn = QPushButton("Back to Login")
        self.back_btn.clicked.connect(self.init_login_ui)

        self.layout.addWidget(QLabel("Student Registration"))
        self.layout.addWidget(self.first_name)
        self.layout.addWidget(self.last_name)
        self.layout.addWidget(self.email)
        self.layout.addWidget(self.password)
        self.layout.addWidget(self.phone)
        self.layout.addWidget(QLabel("Degree:"))
        self.layout.addWidget(self.degree_combo)
        self.layout.addWidget(self.course_label)
        self.layout.addWidget(self.course_scroll_area)
        self.layout.addWidget(self.capture_btn)
        self.layout.addWidget(self.submit_btn)
        self.layout.addWidget(self.back_btn)

    def capture_face(self):
        result = face_logic.capture_and_store_face(self.email.text())
        QMessageBox.information(
            self,
            "Face Capture",
            "Face captured successfully!" if result else "Failed to capture face"
        )

    def submit_registration(self):
        first_name = self.first_name.text()
        last_name = self.last_name.text()
        email = self.email.text()
        password = self.password.text()
        phone = self.phone.text()
        degree = self.degree_combo.currentText()
        selected_courses = [c.text() for c in self.course_checkboxes if c.isChecked()]

        errors = []
        if len(first_name) <= 5:
            errors.append("First name should be more than 5 characters.")
        if not email.endswith("@gmail.com"):
            errors.append("Email should end with '@gmail.com'.")
        if len(password) <= 8:
            errors.append("Password should be more than 8 characters.")
        if len(phone) != 10 or not phone.isdigit():
            errors.append("Phone number should be exactly 10 digits.")
        if degree == "Select Degree":
            errors.append("Please select a degree.")
        if not selected_courses:
            errors.append("Please select at least one course.")

        if errors:
            QMessageBox.warning(self, "Validation Errors", "\n".join(errors))
            return

        student = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            "phone": phone,
            "degree": degree,
            "courses": selected_courses,
        }

        if db_manager.register_student(student):
            QMessageBox.information(self, "Success", "Registered Successfully!")
            self.init_login_ui()
        else:
            QMessageBox.warning(self, "Error", "Registration Failed!")

    def authenticate(self):
        email = self.email_input.text()
        password = self.password_input.text()

        if db_manager.authenticate_student(email, password):
            self.load_dashboard(email)
        else:
            QMessageBox.warning(self, "Error", "Invalid credentials!")

    def load_dashboard(self, email):
        self.clear_layout()
        self.logged_in_email = email
        self.period_headers = period_config.get_period_headers()

        self.timetable = QTableWidget(5, len(self.period_headers))
        self.timetable.setHorizontalHeaderLabels(self.period_headers)
        self.timetable.setVerticalHeaderLabels(["Mon", "Tue", "Wed", "Thu", "Fri"])
        self.timetable.setEditTriggers(QTableWidget.NoEditTriggers)

        timetable_data = db_manager.load_timetable()
        if len(timetable_data) != 5:
            timetable_data = [["" for _ in range(len(self.period_headers))] for _ in range(5)]

        for row in range(5):
            for col in range(len(self.period_headers)):
                subject = timetable_data[row][col]
                if subject:
                    item = QTableWidgetItem(subject)
                    item.setBackground(QColor(173, 216, 230))
                    self.timetable.setItem(row, col, item)

        self.first_name = db_manager.get_first_name(email)
        self.last_name = db_manager.get_last_name(email)

        welcome = QLabel(f"Welcome, {self.first_name} {self.last_name}")
        self.layout.addWidget(welcome)
        self.layout.addWidget(self.timetable)

        self.timetable.cellDoubleClicked.connect(self.handle_period_click)

    def handle_period_click(self, row, col):
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            QMessageBox.warning(self, "Camera Error", "Failed to capture frame.")
            return

        phone_detected = phone_pixel_detection.detect_phone(frame)
        face_verified = face_logic.verify_face(self.logged_in_email)

        if face_verified and not phone_detected:
            self.clear_layout()
            self.showFullScreen()
            self.show_mini_screen()
            db_manager.mark_attendance(self.logged_in_email, row, col)
            QMessageBox.information(self, "Attendance", "Attendance Marked. Class Started.")
            self.start_class_timer(50 * 60)  # 50 minutes class time
            self.start_participation_monitor()

        # Open the fullscreen window
            if not hasattr(self, 'fullscreen_window') or self.fullscreen_window is None:
                self.fullscreen_window = FullscreenWindow()
                self.fullscreen_window.show()

        else:
            reasons = []
            if not face_verified:
                reasons.append("Face verification failed")
            if phone_detected:
                reasons.append("Phone screen detected")
            QMessageBox.warning(self, "Verification Failed", "\n".join(reasons))


    def show_mini_screen(self):
        self.mini_screen_window = QWidget(self, Qt.Window | Qt.FramelessWindowHint)
        self.mini_screen_window.setStyleSheet("background-color: black;")
        self.mini_screen_window.setFixedSize(320, 240)

        layout = QVBoxLayout()
        self.video_label = QLabel()
        self.video_label.setStyleSheet("background-color: #000;")
        layout.addWidget(self.video_label)

        control_layout = QHBoxLayout()
        self.camera_btn = QPushButton("Turn On Camera")
        self.camera_btn.clicked.connect(self.toggle_camera)
        self.mic_btn = QPushButton("Turn On Mic")
        self.mic_btn.clicked.connect(self.toggle_mic)

        control_layout.addWidget(self.camera_btn)
        control_layout.addWidget(self.mic_btn)
        layout.addLayout(control_layout)

        self.mini_screen_window.setLayout(layout)

        screen_rect = QDesktopWidget().availableGeometry()
        x = screen_rect.right() - self.mini_screen_window.width() - 20
        y = screen_rect.bottom() - self.mini_screen_window.height() - 40
        self.mini_screen_window.move(x, y)
        self.mini_screen_window.show()

        self.start_video_audio_stream()

    def start_video_audio_stream(self):
        self.running = True
        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.video_socket.bind(('0.0.0.0', 5000))
        threading.Thread(target=self.receive_video, daemon=True).start()

        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audio_socket.bind(('0.0.0.0', 5001))
        threading.Thread(target=self.receive_audio, daemon=True).start()

    def receive_video(self):
        buffer = b''
        while self.running:
            try:
                packet, _ = self.video_socket.recvfrom(65536)
                if packet == b"<END>":
                    np_arr = np.frombuffer(buffer, dtype=np.uint8)
                    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
                    if frame is not None:
                        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb_image.shape
                        qt_img = QImage(rgb_image.data, w, h, ch * w, QImage.Format_RGB888)
                    # Use Qt's signal/slot mechanism to update UI from another thread
                    # This is the key fix for flickering
                        QApplication.processEvents()  # Add this line
                        self.video_label.setPixmap(QPixmap.fromImage(qt_img))
                    buffer = b''
                else:
                    buffer += packet
            except Exception as e:
                print("Video error:", e)

    def receive_audio(self):
        audio = pyaudio.PyAudio()
        self.audio_stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            output=True,
            frames_per_buffer=1024
        )

        while self.running:
            try:
                data, _ = self.audio_socket.recvfrom(2048)
                self.audio_stream.write(data)
            except Exception as e:
                print("Audio error:", e)

        self.audio_stream.stop_stream()
        self.audio_stream.close()
        audio.terminate()


    def toggle_camera(self):
        self.camera_btn.setText("Turn Off Camera" if self.camera_btn.text() == "Turn On Camera" else "Turn On Camera")

    def toggle_mic(self):
        if self.mic_btn.text() == "Turn On Mic":
            self.mic_btn.setText("Turn Off Mic")
            self.start_local_mic_stream()  # Start playing local mic audio
        else:
            self.mic_btn.setText("Turn On Mic")
            self.stop_local_mic_stream()  # Stop playing local mic audio

    def start_local_mic_stream(self):
        """Start streaming microphone audio locally."""
        audio = pyaudio.PyAudio()
    
    # Initialize the microphone audio stream
        self.local_audio_stream = audio.open(format=pyaudio.paInt16,
                                         channels=1,
                                         rate=44100,
                                         input=True,
                                         frames_per_buffer=1024)
    
    # Initialize the audio playback stream for local output
        self.local_audio_playback_stream = audio.open(format=pyaudio.paInt16,
                                                 channels=1,
                                                 rate=44100,
                                                 output=True,
                                                 frames_per_buffer=1024)
    
    # Start a thread to capture and play the local mic audio
        self.local_mic_thread = threading.Thread(target=self.play_local_mic_audio)
        self.local_mic_thread.daemon = True
        self.local_mic_thread.start()

    def stop_local_mic_stream(self):
        """Stop streaming microphone audio locally."""
        if hasattr(self, 'local_audio_stream'):
            self.local_audio_stream.stop_stream()
            self.local_audio_stream.close()
    
        if hasattr(self, 'local_audio_playback_stream'):
            self.local_audio_playback_stream.stop_stream()
            self.local_audio_playback_stream.close()

    def play_local_mic_audio(self):
        """Capture and play local mic audio in real-time."""
        while True:
            data = self.local_audio_stream.read(1024)
            self.local_audio_playback_stream.write(data)



    def start_class_timer(self, remaining_time):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_class_time)
        self.timer.start(1000)
        self.time_left = remaining_time

    def update_class_time(self):
        minutes, seconds = divmod(self.time_left, 60)
        self.setWindowTitle(f"Class Time Left: {minutes:02}:{seconds:02}")
        self.time_left -= 1
        if self.time_left < 0:
            self.timer.stop()
            if self.participation_monitor:
                self.participation_monitor.stop()

    def start_participation_monitor(self):
        self.participation_monitor = ParticipationMonitor(self.logged_in_email, interval=30)
        self.participation_monitor.alert.connect(self.show_participation_alert)
        self.participation_monitor.start()

    def show_participation_alert(self, message):
        QMessageBox.warning(self, "Inactivity Alert", message)

    def clear_layout(self):
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    portal = StudentPortal()
    portal.show()
    sys.exit(app.exec_())