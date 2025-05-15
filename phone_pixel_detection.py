<<<<<<< HEAD
import cv2
import numpy as np
import time
import threading
import simpleaudio as sa

# =================== Settings ===================
USE_YOLO = False
DETECTION_INTERVAL = 0.5  # seconds
RESIZE_DIMENSIONS = (320, 240)
SOUND_PATH = "alert.wav"

# Detection smoothing
DETECTION_BUFFER_SIZE = 5
DETECTION_THRESHOLD = 3  # trigger if >= this many out of 5 frames detect phone

# =================================================
model = None
last_detection_time = 0
last_sound_time = 0
detection_buffer = [False] * DETECTION_BUFFER_SIZE

def play_warning_sound():
    global last_sound_time
    current_time = time.time()
    if current_time - last_sound_time > 5:
        last_sound_time = current_time
        def _play():
            try:
                wave_obj = sa.WaveObject.from_wave_file(SOUND_PATH)
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except Exception as e:
                print(f"[Sound Error] {e}")
        threading.Thread(target=_play, daemon=True).start()

def detect_phone_pixels_opencv(frame, brightness_threshold=190, area_threshold=1200):
    frame = cv2.resize(frame, RESIZE_DIMENSIONS)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    _, bright_mask = cv2.threshold(gray, brightness_threshold, 255, cv2.THRESH_BINARY)

    # Morphological smoothing
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    bright_mask = cv2.morphologyEx(bright_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(bright_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > area_threshold:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h
            if 0.3 < aspect_ratio < 3.5:
                return True

    return False

def detect_phone(frame):
    global last_detection_time

    current_time = time.time()
    if current_time - last_detection_time < DETECTION_INTERVAL:
        return False

    last_detection_time = current_time
    return detect_phone_pixels_opencv(frame)

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        phone_now = detect_phone(frame)

        # Update detection buffer
        detection_buffer.pop(0)
        detection_buffer.append(phone_now)

        # Count True values in buffer
        detected = sum(detection_buffer) >= DETECTION_THRESHOLD

        if detected:
            cv2.putText(frame, "Don't do proxy!", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 4)
            play_warning_sound()
        else:
            cv2.putText(frame, "Clear", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        cv2.imshow("Phone Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
=======
import cv2
import numpy as np
import time
import threading
import simpleaudio as sa

# =================== Settings ===================
USE_YOLO = False
DETECTION_INTERVAL = 0.5  # seconds
RESIZE_DIMENSIONS = (320, 240)
SOUND_PATH = "alert.wav"

# Detection smoothing
DETECTION_BUFFER_SIZE = 5
DETECTION_THRESHOLD = 3  # trigger if >= this many out of 5 frames detect phone

# =================================================
model = None
last_detection_time = 0
last_sound_time = 0
detection_buffer = [False] * DETECTION_BUFFER_SIZE

def play_warning_sound():
    global last_sound_time
    current_time = time.time()
    if current_time - last_sound_time > 5:
        last_sound_time = current_time
        def _play():
            try:
                wave_obj = sa.WaveObject.from_wave_file(SOUND_PATH)
                play_obj = wave_obj.play()
                play_obj.wait_done()
            except Exception as e:
                print(f"[Sound Error] {e}")
        threading.Thread(target=_play, daemon=True).start()

def detect_phone_pixels_opencv(frame, brightness_threshold=190, area_threshold=1200):
    frame = cv2.resize(frame, RESIZE_DIMENSIONS)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    _, bright_mask = cv2.threshold(gray, brightness_threshold, 255, cv2.THRESH_BINARY)

    # Morphological smoothing
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    bright_mask = cv2.morphologyEx(bright_mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(bright_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > area_threshold:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h
            if 0.3 < aspect_ratio < 3.5:
                return True

    return False

def detect_phone(frame):
    global last_detection_time

    current_time = time.time()
    if current_time - last_detection_time < DETECTION_INTERVAL:
        return False

    last_detection_time = current_time
    return detect_phone_pixels_opencv(frame)

if __name__ == "__main__":
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        phone_now = detect_phone(frame)

        # Update detection buffer
        detection_buffer.pop(0)
        detection_buffer.append(phone_now)

        # Count True values in buffer
        detected = sum(detection_buffer) >= DETECTION_THRESHOLD

        if detected:
            cv2.putText(frame, "Don't do proxy!", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 4)
            play_warning_sound()
        else:
            cv2.putText(frame, "Clear", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        cv2.imshow("Phone Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
>>>>>>> 027277a (Initial commit)
