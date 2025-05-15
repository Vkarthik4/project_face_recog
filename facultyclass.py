<<<<<<< HEAD
import sys
import threading
import socket
import cv2
import numpy as np
import pyaudio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

class FacultyClass(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Faculty Class")
        self.setGeometry(100, 100, 600, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Center-aligned video preview
        self.video_label = QLabel("Camera Preview")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(300)  # Set minimum height for better preview
        self.layout.addWidget(self.video_label)

        self.camera_btn = QPushButton("Turn On Camera")
        self.camera_btn.clicked.connect(self.toggle_camera)
        self.layout.addWidget(self.camera_btn)

        self.mic_btn = QPushButton("Turn On Mic")
        self.mic_btn.clicked.connect(self.toggle_mic)
        self.layout.addWidget(self.mic_btn)

        # Default IP and ports (localhost test)
        self.student_ip = "127.0.0.1"
        self.port_video = 5000
        self.port_audio = 5001
        
        # Port for fullscreen window communication
        self.fullscreen_port = 5002

        # Stream controls
        self.camera_on = False
        self.mic_on = False
        self.cap = None
        self.audio_stream = None

        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fullscreen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def toggle_camera(self):
        if not self.camera_on:
            self.camera_on = True
            self.camera_btn.setText("Turn Off Camera")
            self.cap = cv2.VideoCapture(0)
            threading.Thread(target=self.stream_video, daemon=True).start()
        else:
            self.camera_on = False
            self.camera_btn.setText("Turn On Camera")
            if self.cap:
                self.cap.release()

    def toggle_mic(self):
        if not self.mic_on:
            self.mic_on = True
            self.mic_btn.setText("Turn Off Mic")
            threading.Thread(target=self.stream_audio, daemon=True).start()
        else:
            self.mic_on = False
            self.mic_btn.setText("Turn On Mic")
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()

    def stream_video(self):
        while self.camera_on:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Send frame to student
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            data = buffer.tobytes()

            # Send in chunks to student
            for i in range(0, len(data), 60000):
                chunk = data[i:i+60000]
                self.video_socket.sendto(chunk, (self.student_ip, self.port_video))
            self.video_socket.sendto(b"<END>", (self.student_ip, self.port_video))
            
            # Also send to fullscreen window (smaller images for faster transfer)
            _, small_buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            small_data = small_buffer.tobytes()
            
            for i in range(0, len(small_data), 60000):
                chunk = small_data[i:i+60000]
                self.fullscreen_socket.sendto(chunk, ("127.0.0.1", self.fullscreen_port))
            self.fullscreen_socket.sendto(b"<END>", ("127.0.0.1", self.fullscreen_port))

            # Show preview on faculty window
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            # Scale pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled_pixmap)
            
            cv2.waitKey(1)

    def stream_audio(self):
        audio = pyaudio.PyAudio()
        self.audio_stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )

        while self.mic_on:
            try:
                data = self.audio_stream.read(1024)
                self.audio_socket.sendto(data, (self.student_ip, self.port_audio))
            except Exception as e:
                print("Audio stream error:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FacultyClass()
    window.show()
=======
import sys
import threading
import socket
import cv2
import numpy as np
import pyaudio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

class FacultyClass(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Faculty Class")
        self.setGeometry(100, 100, 600, 500)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Center-aligned video preview
        self.video_label = QLabel("Camera Preview")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumHeight(300)  # Set minimum height for better preview
        self.layout.addWidget(self.video_label)

        self.camera_btn = QPushButton("Turn On Camera")
        self.camera_btn.clicked.connect(self.toggle_camera)
        self.layout.addWidget(self.camera_btn)

        self.mic_btn = QPushButton("Turn On Mic")
        self.mic_btn.clicked.connect(self.toggle_mic)
        self.layout.addWidget(self.mic_btn)

        # Default IP and ports (localhost test)
        self.student_ip = "127.0.0.1"
        self.port_video = 5000
        self.port_audio = 5001
        
        # Port for fullscreen window communication
        self.fullscreen_port = 5002

        # Stream controls
        self.camera_on = False
        self.mic_on = False
        self.cap = None
        self.audio_stream = None

        self.video_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.audio_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.fullscreen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def toggle_camera(self):
        if not self.camera_on:
            self.camera_on = True
            self.camera_btn.setText("Turn Off Camera")
            self.cap = cv2.VideoCapture(0)
            threading.Thread(target=self.stream_video, daemon=True).start()
        else:
            self.camera_on = False
            self.camera_btn.setText("Turn On Camera")
            if self.cap:
                self.cap.release()

    def toggle_mic(self):
        if not self.mic_on:
            self.mic_on = True
            self.mic_btn.setText("Turn Off Mic")
            threading.Thread(target=self.stream_audio, daemon=True).start()
        else:
            self.mic_on = False
            self.mic_btn.setText("Turn On Mic")
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()

    def stream_video(self):
        while self.camera_on:
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Send frame to student
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
            data = buffer.tobytes()

            # Send in chunks to student
            for i in range(0, len(data), 60000):
                chunk = data[i:i+60000]
                self.video_socket.sendto(chunk, (self.student_ip, self.port_video))
            self.video_socket.sendto(b"<END>", (self.student_ip, self.port_video))
            
            # Also send to fullscreen window (smaller images for faster transfer)
            _, small_buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            small_data = small_buffer.tobytes()
            
            for i in range(0, len(small_data), 60000):
                chunk = small_data[i:i+60000]
                self.fullscreen_socket.sendto(chunk, ("127.0.0.1", self.fullscreen_port))
            self.fullscreen_socket.sendto(b"<END>", ("127.0.0.1", self.fullscreen_port))

            # Show preview on faculty window
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qimg = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)
            
            # Scale pixmap to fit the label while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.video_label.setPixmap(scaled_pixmap)
            
            cv2.waitKey(1)

    def stream_audio(self):
        audio = pyaudio.PyAudio()
        self.audio_stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024
        )

        while self.mic_on:
            try:
                data = self.audio_stream.read(1024)
                self.audio_socket.sendto(data, (self.student_ip, self.port_audio))
            except Exception as e:
                print("Audio stream error:", e)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FacultyClass()
    window.show()
>>>>>>> 027277a (Initial commit)
    sys.exit(app.exec_())