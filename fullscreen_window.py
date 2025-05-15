<<<<<<< HEAD
import sys
import cv2
import numpy as np
import socket
import threading
import pyaudio
import dlib
from ultralytics import YOLO
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtCore import QTime

from models.mobilefacenet import MobileFaceNet

CAMO_DEVICE_INDEX = 1  # Change as needed

class FrameReceiver(QObject):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, port=5002):
        super().__init__()
        self.port = port
        self.running = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("0.0.0.0", self.port))
        self.buffer_size = 65536  # Increased buffer size for UDP
        # Set socket timeout to avoid blocking
        self.socket.settimeout(0.1)

    def start_receiving(self):
        self.running = True
        threading.Thread(target=self.receive_frames, daemon=True).start()

    def stop_receiving(self):
        self.running = False

    def receive_frames(self):
        data_chunks = []
        while self.running:
            try:
                chunk, _ = self.socket.recvfrom(self.buffer_size)
                if chunk == b"<END>":
                    if data_chunks:
                        data = b''.join(data_chunks)
                        img_array = np.frombuffer(data, dtype=np.uint8)
                        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        if frame is not None:
                            # Resize frame to reduce processing load
                            frame = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75) 
                            self.frame_ready.emit(frame)
                        data_chunks = []
                else:
                    data_chunks.append(chunk)
            except socket.timeout:
                # Just continue on timeout
                pass
            except Exception as e:
                print(f"Error receiving frame: {e}")
                # Short sleep to prevent CPU overuse on error
                threading.Event().wait(0.01)

class CameraControl(QObject):
    def __init__(self, student_ip="127.0.0.1", port=5005, cam_device_index=CAMO_DEVICE_INDEX):
        super().__init__()
        self.student_ip = student_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cam_device_index = cam_device_index
        self.student_cam = None

    def toggle_camera(self, state):
        if state:
            try:
                self.student_cam = cv2.VideoCapture(self.cam_device_index)
                if not self.student_cam.isOpened():
                    print("Failed to open Camo webcam stream")
                    return False
                
                # Configure camera for better performance
                self.student_cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.student_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.student_cam.set(cv2.CAP_PROP_FPS, 30)
                
                print("Camo webcam stream started")
                return True
            except Exception as e:
                print(f"Failed to start Camo webcam stream: {e}")
                return False
        else:
            if self.student_cam:
                self.student_cam.release()
                print("Camo webcam stream stopped")
            return True

class MicrophoneControl(QObject):
    def __init__(self):
        super().__init__()
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream_input = None
        self.stream_output = None
        self.microphone_on = False
        self.audio_buffer = []
        self.buffer_size = 1024  # Adjusted buffer size

    def toggle_microphone(self, state):
        if state:
            self.microphone_on = True
            self.stream_input = self.pyaudio_instance.open(format=pyaudio.paInt16,
                                                           channels=1,
                                                           rate=44100,
                                                           input=True,
                                                           frames_per_buffer=self.buffer_size)
            self.stream_output = self.pyaudio_instance.open(format=pyaudio.paInt16,
                                                            channels=1,
                                                            rate=44100,
                                                            output=True,
                                                            frames_per_buffer=self.buffer_size)
            print("Microphone On")
            threading.Thread(target=self._process_audio, daemon=True).start()
        else:
            self.microphone_on = False
            if self.stream_input:
                self.stream_input.stop_stream()
                self.stream_input.close()
            if self.stream_output:
                self.stream_output.stop_stream()
                self.stream_output.close()
            print("Microphone Off")

    def _process_audio(self):
        while self.microphone_on:
            try:
                audio_data = self.stream_input.read(self.buffer_size, exception_on_overflow=False)
                self.stream_output.write(audio_data)
            except Exception as e:
                print(f"Audio processing error: {e}")
                threading.Event().wait(0.01)

class FullscreenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Faculty Fullscreen Camera View")
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fullscreen_label = QLabel(self)
        self.fullscreen_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.fullscreen_label)

        self.mini_container = QWidget(self)
        self.mini_container.setFixedSize(300, 240)
        self.mini_container.setStyleSheet("background-color: rgba(0, 0, 0, 80); border: 1px solid white;")

        mini_layout = QVBoxLayout(self.mini_container)
        mini_layout.setContentsMargins(5, 5, 5, 5)

        self.mini_title = QLabel("Student Camera Control")
        self.mini_title.setFont(QFont("Arial", 12))
        self.mini_title.setStyleSheet("color: white;")
        self.mini_title.setAlignment(Qt.AlignCenter)
        mini_layout.addWidget(self.mini_title)

        self.student_cam_preview = QLabel("No student camera")
        self.student_cam_preview.setStyleSheet("color: white; border: 1px dashed gray;")
        self.student_cam_preview.setAlignment(Qt.AlignCenter)
        self.student_cam_preview.setMinimumHeight(150)
        mini_layout.addWidget(self.student_cam_preview)

        self.camera_btn = QPushButton("Turn On Student Camera")
        self.camera_btn.setStyleSheet("background-color: #2a9d8f; color: white; padding: 5px; border-radius: 5px;")
        self.camera_btn.clicked.connect(self.toggle_student_camera)
        mini_layout.addWidget(self.camera_btn)

        self.mic_btn = QPushButton("Turn On Microphone")
        self.mic_btn.setStyleSheet("background-color: #2a9d8f; color: white; padding: 5px; border-radius: 5px;")
        self.mic_btn.clicked.connect(self.toggle_microphone)
        mini_layout.addWidget(self.mic_btn)

        self.student_camera_on = False
        self.microphone_control = MicrophoneControl()
        self.camera_control = CameraControl(cam_device_index=CAMO_DEVICE_INDEX)

        self.timer_label = QLabel("50:00", self)
        self.timer_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); padding: 8px; border-radius: 10px;")
        self.timer_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.timer_label.adjustSize()
        self.timer_label.setAlignment(Qt.AlignRight)

        self.showFullScreen()
        self.position_elements()

        self.receiver = FrameReceiver()
        self.receiver.frame_ready.connect(self.update_frame)
        self.receiver.start_receiving()

        self.time_remaining = 50 * 60
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_timer)
        self.countdown_timer.start(1000)

        self.student_cam = None
        self.student_cam_timer = QTimer()
        self.student_cam_timer.timeout.connect(self.read_student_camera_frame)
        
        # Optimize AI model loading - make it happen in a separate thread to avoid UI blocking
        self.face_detection_ready = False
        threading.Thread(target=self.load_ai_models, daemon=True).start()
        
        # Frame processing optimization
        self.frame_skip_counter = 0
        self.process_every_n_frames = 5  # Process every 5th frame for face detection
        self.last_frame = None
        self.last_processed_frame = None
        self.student_is_active = False  # Tracks if student is active in the frame
        
        # Activity tracking
        self.activity_timestamps = []
        self.activity_duration = 0
        self.activity_percentage = 0

    def load_ai_models(self):
        try:
            self.yolo_model = YOLO("yolov8n.pt")
            self.face_recognizer = MobileFaceNet()
            self.dlib_detector = dlib.get_frontal_face_detector()
            self.shape_predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
            self.face_detection_ready = True
            print("AI models loaded successfully")
        except Exception as e:
            print(f"Failed to load AI models: {e}")

    def position_elements(self):
        screen_size = self.size()
        mini_size = self.mini_container.size()
        self.mini_container.move(screen_size.width() - mini_size.width() - 30,
                                 screen_size.height() - mini_size.height() - 30)
        self.timer_label.move(screen_size.width() - self.timer_label.width() - 30, 30)

    def toggle_student_camera(self):
        self.student_camera_on = not self.student_camera_on
        if self.student_camera_on:
            self.camera_btn.setText("Turn Off Student Camera")
            if self.camera_control.toggle_camera(True):
                self.student_cam = cv2.VideoCapture(CAMO_DEVICE_INDEX)
                if self.student_cam.isOpened():
                    # Set student camera properties for better performance
                    self.student_cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.student_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.student_cam.set(cv2.CAP_PROP_FPS, 30)
                    # Use a faster timer interval for smoother video
                    self.student_cam_timer.start(33)  # ~30 fps
                else:
                    self.student_cam_preview.setText("Camera not found!")
        else:
            self.camera_btn.setText("Turn On Student Camera")
            if self.camera_control.toggle_camera(False):
                if self.student_cam_timer.isActive():
                    self.student_cam_timer.stop()
                if self.student_cam:
                    self.student_cam.release()
                    self.student_cam = None
                self.student_cam_preview.setText("No student camera")

    def toggle_microphone(self):
        self.microphone_control.toggle_microphone(not self.microphone_control.microphone_on)
        if self.microphone_control.microphone_on:
            self.mic_btn.setText("Turn Off Microphone")
        else:
            self.mic_btn.setText("Turn On Microphone")

    def read_student_camera_frame(self):
        if self.student_cam:
            ret, frame = self.student_cam.read()
            if ret:
                # Store the frame without processing
                self.last_frame = frame.copy()
                
                # Skip frames to reduce processing load
                self.frame_skip_counter += 1
                if self.frame_skip_counter >= self.process_every_n_frames:
                    self.frame_skip_counter = 0
                    # Process frame for face detection in background thread if models are loaded
                    if self.face_detection_ready:
                        threading.Thread(target=self.process_face_detection, 
                                        args=(frame.copy(),), daemon=True).start()
                
                # Always update the display with the latest frame
                self.update_student_camera(frame)

    def process_face_detection(self, frame):
        try:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            
            # Track previous frame for motion detection
            if not hasattr(self, 'prev_frame'):
                self.prev_frame = small_frame.copy()
                self.prev_gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                
            # Convert current frame to grayscale for motion detection
            current_gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            # Initialize active status variables
            person_detected = False
            face_detected = False
            motion_detected = False
            
            # Run YOLOv8 model for person detection
            results = self.yolo_model(small_frame, verbose=False)
            
            # Check for person detection
            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    if cls == 0 and conf > 0.50:  # Class 0 is 'person' in YOLOv8 with good confidence
                        person_detected = True
                        break
                if person_detected:
                    break
            
            # Use dlib for face detection (more reliable for engagement)
            faces = self.dlib_detector(current_gray)
            face_detected = len(faces) > 0
            
            # Check for facial landmarks if face detected
            face_frontal = False
            if face_detected:
                for face in faces:
                    shape = self.shape_predictor(current_gray, face)
                    
                    # Calculate facial orientation by comparing eye positions
                    left_eye_x = (shape.part(36).x + shape.part(39).x) / 2
                    right_eye_x = (shape.part(42).x + shape.part(45).x) / 2
                    left_eye_y = (shape.part(36).y + shape.part(39).y) / 2
                    right_eye_y = (shape.part(42).y + shape.part(45).y) / 2
                    
                    # Check if eyes are roughly at the same height (face is frontal)
                    if abs(right_eye_y - left_eye_y) < 10:
                        face_frontal = True
            
            # Detect motion between frames
            if hasattr(self, 'prev_gray'):
                # Calculate absolute difference between current and previous frame
                frame_diff = cv2.absdiff(current_gray, self.prev_gray)
                _, motion_mask = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
                motion_pixels = cv2.countNonZero(motion_mask)
                
                # Consider motion detected if more than 1% of pixels changed
                motion_threshold = small_frame.shape[0] * small_frame.shape[1] * 0.01
                motion_detected = motion_pixels > motion_threshold
            
            # Update previous frame for next comparison
            self.prev_gray = current_gray.copy()
            
            # Determine if student is active based on multiple factors
            # Student is considered active if a person is detected AND either:
            # - A face is detected in frontal position, OR
            # - Significant motion is detected
            self.student_is_active = person_detected and (face_frontal or motion_detected)
            
            # Track activity time
            current_time = QTimer.currentTime().msecsSinceStartOfDay() / 1000  # in seconds
            if hasattr(self, 'last_activity_check_time'):
                time_diff = current_time - self.last_activity_check_time
                if self.student_is_active:
                    self.activity_duration += time_diff
                    self.activity_timestamps.append(current_time)
                    # Keep only last 5 minutes of timestamps
                    self.activity_timestamps = [t for t in self.activity_timestamps 
                                               if current_time - t <= 300]
            self.last_activity_check_time = current_time
            
            # Calculate activity percentage over last 5 minutes
            if self.time_remaining < 50*60:  # Only calculate after session has started
                elapsed_time = 50*60 - self.time_remaining
                elapsed_time = min(elapsed_time, 300)  # Use at most 5 minutes or elapsed time
                if elapsed_time > 0:
                    self.activity_percentage = min(100, int((self.activity_duration / elapsed_time) * 100))
            
            # Draw detection results on the frame
            processed_frame = frame.copy()
            if self.student_is_active:
                status_color = (0, 255, 0)  # Green
                status_text = "ACTIVE"
            else:
                status_color = (0, 0, 255)  # Red
                status_text = "NOT ACTIVE"
                
            # Add status indicators
            cv2.putText(processed_frame, status_text, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2, cv2.LINE_AA)
            
            # Add detection indicators
            indicators = []
            if person_detected: indicators.append("Person")
            if face_detected: indicators.append("Face" + (" (Frontal)" if face_frontal else ""))
            if motion_detected: indicators.append("Motion")
            
            indicator_text = ", ".join(indicators)
            cv2.putText(processed_frame, indicator_text, (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Add participation metrics
            cv2.putText(processed_frame, f"Participation: {self.activity_percentage}%", 
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1, cv2.LINE_AA)
            
            # Store the processed frame
            self.last_processed_frame = processed_frame
            
        except Exception as e:
            print(f"Face detection error: {e}")
            import traceback
            traceback.print_exc()

    def update_student_camera(self, frame):
        try:
            # Use the processed frame if available, otherwise use the raw frame
            display_frame = self.last_processed_frame if self.last_processed_frame is not None else frame
            
            # Add active/inactive text based on student activity status
            if not self.last_processed_frame:  # Only add text if it wasn't already added in processing
                if self.student_is_active:
                    cv2.putText(display_frame, "ACTIVE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2, cv2.LINE_AA)
                else:
                    cv2.putText(display_frame, "NOT ACTIVE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255), 2, cv2.LINE_AA)

            # Convert frame to QImage
            rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0],
                          rgb_image.strides[0], QImage.Format_RGB888)
            
            # Scale image to fit preview window
            student_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.student_cam_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Set the pixmap to display in the student camera preview window
            self.student_cam_preview.setPixmap(student_pixmap)
        except Exception as e:
            print(f"Update mini screen error: {e}")

    def update_frame(self, frame):
        # Convert to RGB format for Qt
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create QImage - use frame size to avoid copying data
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale while preserving aspect ratio
        pixmap = QPixmap.fromImage(qt_image).scaled(
            self.fullscreen_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.fullscreen_label.setPixmap(pixmap)

    def update_timer(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            minutes, seconds = divmod(self.time_remaining, 60)
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
            
    def keyPressEvent(self, event):
        # Exit fullscreen on Escape key press
        if event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
                self.position_elements()
        super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FullscreenWindow()
=======
import sys
import cv2
import numpy as np
import socket
import threading
import pyaudio
import dlib
from ultralytics import YOLO
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication, QPushButton
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt5.QtCore import QTime

from models.mobilefacenet import MobileFaceNet

CAMO_DEVICE_INDEX = 1  # Change as needed

class FrameReceiver(QObject):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, port=5002):
        super().__init__()
        self.port = port
        self.running = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(("0.0.0.0", self.port))
        self.buffer_size = 65536  # Increased buffer size for UDP
        # Set socket timeout to avoid blocking
        self.socket.settimeout(0.1)

    def start_receiving(self):
        self.running = True
        threading.Thread(target=self.receive_frames, daemon=True).start()

    def stop_receiving(self):
        self.running = False

    def receive_frames(self):
        data_chunks = []
        while self.running:
            try:
                chunk, _ = self.socket.recvfrom(self.buffer_size)
                if chunk == b"<END>":
                    if data_chunks:
                        data = b''.join(data_chunks)
                        img_array = np.frombuffer(data, dtype=np.uint8)
                        frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                        if frame is not None:
                            # Resize frame to reduce processing load
                            frame = cv2.resize(frame, (0, 0), fx=0.75, fy=0.75) 
                            self.frame_ready.emit(frame)
                        data_chunks = []
                else:
                    data_chunks.append(chunk)
            except socket.timeout:
                # Just continue on timeout
                pass
            except Exception as e:
                print(f"Error receiving frame: {e}")
                # Short sleep to prevent CPU overuse on error
                threading.Event().wait(0.01)

class CameraControl(QObject):
    def __init__(self, student_ip="127.0.0.1", port=5005, cam_device_index=CAMO_DEVICE_INDEX):
        super().__init__()
        self.student_ip = student_ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.cam_device_index = cam_device_index
        self.student_cam = None

    def toggle_camera(self, state):
        if state:
            try:
                self.student_cam = cv2.VideoCapture(self.cam_device_index)
                if not self.student_cam.isOpened():
                    print("Failed to open Camo webcam stream")
                    return False
                
                # Configure camera for better performance
                self.student_cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.student_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.student_cam.set(cv2.CAP_PROP_FPS, 30)
                
                print("Camo webcam stream started")
                return True
            except Exception as e:
                print(f"Failed to start Camo webcam stream: {e}")
                return False
        else:
            if self.student_cam:
                self.student_cam.release()
                print("Camo webcam stream stopped")
            return True

class MicrophoneControl(QObject):
    def __init__(self):
        super().__init__()
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream_input = None
        self.stream_output = None
        self.microphone_on = False
        self.audio_buffer = []
        self.buffer_size = 1024  # Adjusted buffer size

    def toggle_microphone(self, state):
        if state:
            self.microphone_on = True
            self.stream_input = self.pyaudio_instance.open(format=pyaudio.paInt16,
                                                           channels=1,
                                                           rate=44100,
                                                           input=True,
                                                           frames_per_buffer=self.buffer_size)
            self.stream_output = self.pyaudio_instance.open(format=pyaudio.paInt16,
                                                            channels=1,
                                                            rate=44100,
                                                            output=True,
                                                            frames_per_buffer=self.buffer_size)
            print("Microphone On")
            threading.Thread(target=self._process_audio, daemon=True).start()
        else:
            self.microphone_on = False
            if self.stream_input:
                self.stream_input.stop_stream()
                self.stream_input.close()
            if self.stream_output:
                self.stream_output.stop_stream()
                self.stream_output.close()
            print("Microphone Off")

    def _process_audio(self):
        while self.microphone_on:
            try:
                audio_data = self.stream_input.read(self.buffer_size, exception_on_overflow=False)
                self.stream_output.write(audio_data)
            except Exception as e:
                print(f"Audio processing error: {e}")
                threading.Event().wait(0.01)

class FullscreenWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Faculty Fullscreen Camera View")
        self.setStyleSheet("background-color: black;")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.fullscreen_label = QLabel(self)
        self.fullscreen_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.fullscreen_label)

        self.mini_container = QWidget(self)
        self.mini_container.setFixedSize(300, 240)
        self.mini_container.setStyleSheet("background-color: rgba(0, 0, 0, 80); border: 1px solid white;")

        mini_layout = QVBoxLayout(self.mini_container)
        mini_layout.setContentsMargins(5, 5, 5, 5)

        self.mini_title = QLabel("Student Camera Control")
        self.mini_title.setFont(QFont("Arial", 12))
        self.mini_title.setStyleSheet("color: white;")
        self.mini_title.setAlignment(Qt.AlignCenter)
        mini_layout.addWidget(self.mini_title)

        self.student_cam_preview = QLabel("No student camera")
        self.student_cam_preview.setStyleSheet("color: white; border: 1px dashed gray;")
        self.student_cam_preview.setAlignment(Qt.AlignCenter)
        self.student_cam_preview.setMinimumHeight(150)
        mini_layout.addWidget(self.student_cam_preview)

        self.camera_btn = QPushButton("Turn On Student Camera")
        self.camera_btn.setStyleSheet("background-color: #2a9d8f; color: white; padding: 5px; border-radius: 5px;")
        self.camera_btn.clicked.connect(self.toggle_student_camera)
        mini_layout.addWidget(self.camera_btn)

        self.mic_btn = QPushButton("Turn On Microphone")
        self.mic_btn.setStyleSheet("background-color: #2a9d8f; color: white; padding: 5px; border-radius: 5px;")
        self.mic_btn.clicked.connect(self.toggle_microphone)
        mini_layout.addWidget(self.mic_btn)

        self.student_camera_on = False
        self.microphone_control = MicrophoneControl()
        self.camera_control = CameraControl(cam_device_index=CAMO_DEVICE_INDEX)

        self.timer_label = QLabel("50:00", self)
        self.timer_label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); padding: 8px; border-radius: 10px;")
        self.timer_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.timer_label.adjustSize()
        self.timer_label.setAlignment(Qt.AlignRight)

        self.showFullScreen()
        self.position_elements()

        self.receiver = FrameReceiver()
        self.receiver.frame_ready.connect(self.update_frame)
        self.receiver.start_receiving()

        self.time_remaining = 50 * 60
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_timer)
        self.countdown_timer.start(1000)

        self.student_cam = None
        self.student_cam_timer = QTimer()
        self.student_cam_timer.timeout.connect(self.read_student_camera_frame)
        
        # Optimize AI model loading - make it happen in a separate thread to avoid UI blocking
        self.face_detection_ready = False
        threading.Thread(target=self.load_ai_models, daemon=True).start()
        
        # Frame processing optimization
        self.frame_skip_counter = 0
        self.process_every_n_frames = 5  # Process every 5th frame for face detection
        self.last_frame = None
        self.last_processed_frame = None
        self.student_is_active = False  # Tracks if student is active in the frame
        
        # Activity tracking
        self.activity_timestamps = []
        self.activity_duration = 0
        self.activity_percentage = 0

    def load_ai_models(self):
        try:
            self.yolo_model = YOLO("yolov8n.pt")
            self.face_recognizer = MobileFaceNet()
            self.dlib_detector = dlib.get_frontal_face_detector()
            self.shape_predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")
            self.face_detection_ready = True
            print("AI models loaded successfully")
        except Exception as e:
            print(f"Failed to load AI models: {e}")

    def position_elements(self):
        screen_size = self.size()
        mini_size = self.mini_container.size()
        self.mini_container.move(screen_size.width() - mini_size.width() - 30,
                                 screen_size.height() - mini_size.height() - 30)
        self.timer_label.move(screen_size.width() - self.timer_label.width() - 30, 30)

    def toggle_student_camera(self):
        self.student_camera_on = not self.student_camera_on
        if self.student_camera_on:
            self.camera_btn.setText("Turn Off Student Camera")
            if self.camera_control.toggle_camera(True):
                self.student_cam = cv2.VideoCapture(CAMO_DEVICE_INDEX)
                if self.student_cam.isOpened():
                    # Set student camera properties for better performance
                    self.student_cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.student_cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.student_cam.set(cv2.CAP_PROP_FPS, 30)
                    # Use a faster timer interval for smoother video
                    self.student_cam_timer.start(33)  # ~30 fps
                else:
                    self.student_cam_preview.setText("Camera not found!")
        else:
            self.camera_btn.setText("Turn On Student Camera")
            if self.camera_control.toggle_camera(False):
                if self.student_cam_timer.isActive():
                    self.student_cam_timer.stop()
                if self.student_cam:
                    self.student_cam.release()
                    self.student_cam = None
                self.student_cam_preview.setText("No student camera")

    def toggle_microphone(self):
        self.microphone_control.toggle_microphone(not self.microphone_control.microphone_on)
        if self.microphone_control.microphone_on:
            self.mic_btn.setText("Turn Off Microphone")
        else:
            self.mic_btn.setText("Turn On Microphone")

    def read_student_camera_frame(self):
        if self.student_cam:
            ret, frame = self.student_cam.read()
            if ret:
                # Store the frame without processing
                self.last_frame = frame.copy()
                
                # Skip frames to reduce processing load
                self.frame_skip_counter += 1
                if self.frame_skip_counter >= self.process_every_n_frames:
                    self.frame_skip_counter = 0
                    # Process frame for face detection in background thread if models are loaded
                    if self.face_detection_ready:
                        threading.Thread(target=self.process_face_detection, 
                                        args=(frame.copy(),), daemon=True).start()
                
                # Always update the display with the latest frame
                self.update_student_camera(frame)

    def process_face_detection(self, frame):
        try:
            # Resize frame for faster processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            
            # Track previous frame for motion detection
            if not hasattr(self, 'prev_frame'):
                self.prev_frame = small_frame.copy()
                self.prev_gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                
            # Convert current frame to grayscale for motion detection
            current_gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
            
            # Initialize active status variables
            person_detected = False
            face_detected = False
            motion_detected = False
            
            # Run YOLOv8 model for person detection
            results = self.yolo_model(small_frame, verbose=False)
            
            # Check for person detection
            for result in results:
                for box in result.boxes:
                    cls = int(box.cls[0])
                    conf = float(box.conf[0])
                    if cls == 0 and conf > 0.50:  # Class 0 is 'person' in YOLOv8 with good confidence
                        person_detected = True
                        break
                if person_detected:
                    break
            
            # Use dlib for face detection (more reliable for engagement)
            faces = self.dlib_detector(current_gray)
            face_detected = len(faces) > 0
            
            # Check for facial landmarks if face detected
            face_frontal = False
            if face_detected:
                for face in faces:
                    shape = self.shape_predictor(current_gray, face)
                    
                    # Calculate facial orientation by comparing eye positions
                    left_eye_x = (shape.part(36).x + shape.part(39).x) / 2
                    right_eye_x = (shape.part(42).x + shape.part(45).x) / 2
                    left_eye_y = (shape.part(36).y + shape.part(39).y) / 2
                    right_eye_y = (shape.part(42).y + shape.part(45).y) / 2
                    
                    # Check if eyes are roughly at the same height (face is frontal)
                    if abs(right_eye_y - left_eye_y) < 10:
                        face_frontal = True
            
            # Detect motion between frames
            if hasattr(self, 'prev_gray'):
                # Calculate absolute difference between current and previous frame
                frame_diff = cv2.absdiff(current_gray, self.prev_gray)
                _, motion_mask = cv2.threshold(frame_diff, 25, 255, cv2.THRESH_BINARY)
                motion_pixels = cv2.countNonZero(motion_mask)
                
                # Consider motion detected if more than 1% of pixels changed
                motion_threshold = small_frame.shape[0] * small_frame.shape[1] * 0.01
                motion_detected = motion_pixels > motion_threshold
            
            # Update previous frame for next comparison
            self.prev_gray = current_gray.copy()
            
            # Determine if student is active based on multiple factors
            # Student is considered active if a person is detected AND either:
            # - A face is detected in frontal position, OR
            # - Significant motion is detected
            self.student_is_active = person_detected and (face_frontal or motion_detected)
            
            # Track activity time
            current_time = QTimer.currentTime().msecsSinceStartOfDay() / 1000  # in seconds
            if hasattr(self, 'last_activity_check_time'):
                time_diff = current_time - self.last_activity_check_time
                if self.student_is_active:
                    self.activity_duration += time_diff
                    self.activity_timestamps.append(current_time)
                    # Keep only last 5 minutes of timestamps
                    self.activity_timestamps = [t for t in self.activity_timestamps 
                                               if current_time - t <= 300]
            self.last_activity_check_time = current_time
            
            # Calculate activity percentage over last 5 minutes
            if self.time_remaining < 50*60:  # Only calculate after session has started
                elapsed_time = 50*60 - self.time_remaining
                elapsed_time = min(elapsed_time, 300)  # Use at most 5 minutes or elapsed time
                if elapsed_time > 0:
                    self.activity_percentage = min(100, int((self.activity_duration / elapsed_time) * 100))
            
            # Draw detection results on the frame
            processed_frame = frame.copy()
            if self.student_is_active:
                status_color = (0, 255, 0)  # Green
                status_text = "ACTIVE"
            else:
                status_color = (0, 0, 255)  # Red
                status_text = "NOT ACTIVE"
                
            # Add status indicators
            cv2.putText(processed_frame, status_text, (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2, cv2.LINE_AA)
            
            # Add detection indicators
            indicators = []
            if person_detected: indicators.append("Person")
            if face_detected: indicators.append("Face" + (" (Frontal)" if face_frontal else ""))
            if motion_detected: indicators.append("Motion")
            
            indicator_text = ", ".join(indicators)
            cv2.putText(processed_frame, indicator_text, (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1, cv2.LINE_AA)
            
            # Add participation metrics
            cv2.putText(processed_frame, f"Participation: {self.activity_percentage}%", 
                        (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1, cv2.LINE_AA)
            
            # Store the processed frame
            self.last_processed_frame = processed_frame
            
        except Exception as e:
            print(f"Face detection error: {e}")
            import traceback
            traceback.print_exc()

    def update_student_camera(self, frame):
        try:
            # Use the processed frame if available, otherwise use the raw frame
            display_frame = self.last_processed_frame if self.last_processed_frame is not None else frame
            
            # Add active/inactive text based on student activity status
            if not self.last_processed_frame:  # Only add text if it wasn't already added in processing
                if self.student_is_active:
                    cv2.putText(display_frame, "ACTIVE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 255, 0), 2, cv2.LINE_AA)
                else:
                    cv2.putText(display_frame, "NOT ACTIVE", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1,
                            (0, 0, 255), 2, cv2.LINE_AA)

            # Convert frame to QImage
            rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0],
                          rgb_image.strides[0], QImage.Format_RGB888)
            
            # Scale image to fit preview window
            student_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.student_cam_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
            # Set the pixmap to display in the student camera preview window
            self.student_cam_preview.setPixmap(student_pixmap)
        except Exception as e:
            print(f"Update mini screen error: {e}")

    def update_frame(self, frame):
        # Convert to RGB format for Qt
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create QImage - use frame size to avoid copying data
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        
        # Scale while preserving aspect ratio
        pixmap = QPixmap.fromImage(qt_image).scaled(
            self.fullscreen_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        
        self.fullscreen_label.setPixmap(pixmap)

    def update_timer(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            minutes, seconds = divmod(self.time_remaining, 60)
            self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
            
    def keyPressEvent(self, event):
        # Exit fullscreen on Escape key press
        if event.key() == Qt.Key_Escape:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
                self.position_elements()
        super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FullscreenWindow()
>>>>>>> 027277a (Initial commit)
    sys.exit(app.exec_())