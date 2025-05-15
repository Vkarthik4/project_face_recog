import cv2
import numpy as np
import os
import pickle
import time
import torch
import torch.nn.functional as F
from sklearn.metrics.pairwise import cosine_similarity
from ultralytics import YOLO
from models.mobilefacenet import MobileFaceNet
from phone_pixel_detection import detect_phone
import dlib
import os

# Constants
FRAME_SKIP = 2
RESIZE_DIMENSIONS = (320, 240)
MIN_DETECTION_INTERVAL = 0.5
MAX_EMBEDDING_ATTEMPTS = 5
EMBEDDING_SIZE = 128

# YOLO model for face detection
model = YOLO("yolov8n-face.pt")

# MobileFaceNet model setup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
face_model = MobileFaceNet(embedding_size=EMBEDDING_SIZE)
state_dict = torch.load("models/mobilefacenet_clean.pt", map_location=device)
face_model.load_state_dict(state_dict, strict=False)
face_model.eval()
face_model.to(device)

# dlib face detector and shape predictor for face alignment
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("models/shape_predictor_68_face_landmarks.dat")

# Detection timers
last_detection_time = 0
last_phone_check_time = 0

def preprocess_image(image, fast_mode=False):
    image = cv2.resize(image, RESIZE_DIMENSIONS)
    if fast_mode:
        return image
    image = cv2.convertScaleAbs(image, alpha=1.5, beta=30)
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    merged = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    return sharpened

def extract_face_embedding(image, fast_mode=True):
    global last_detection_time
    current_time = time.time()
    if current_time - last_detection_time < MIN_DETECTION_INTERVAL:
        return None
    last_detection_time = current_time

    image = preprocess_image(image, fast_mode=fast_mode)
    results = model(image, verbose=False, conf=0.5)
    boxes = results[0].boxes.xyxy.cpu().numpy()

    if len(boxes) == 0:
        return None

    x1, y1, x2, y2 = map(int, boxes[0])
    face_crop = image[y1:y2, x1:x2]
    if face_crop.size == 0:
        return None

    face_crop = cv2.resize(face_crop, (112, 112))
    face_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
    face_crop = face_crop.astype(np.float32) / 255.0
    face_crop = (face_crop - 0.5) / 0.5
    face_crop = np.transpose(face_crop, (2, 0, 1))
    face_tensor = torch.tensor(face_crop).unsqueeze(0).to(device)

    with torch.no_grad():
        embedding = face_model(face_tensor)

    return embedding.cpu().numpy().flatten()

def capture_live_face_embedding(max_attempts=MAX_EMBEDDING_ATTEMPTS):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    embedding = None
    attempts = 0
    frame_count = 0
    global last_phone_check_time

    cv2.namedWindow("Face Capture", cv2.WINDOW_NORMAL)
    print("▶️ Live video started. Press 'c' to capture your face, or 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1

        if frame_count % FRAME_SKIP != 0:
            cv2.imshow("Face Capture", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        phone_detected = False
        if time.time() - last_phone_check_time > 1.0:
            phone_detected = detect_phone(frame)
            last_phone_check_time = time.time()

        if phone_detected:
            cv2.putText(frame, "Phone Detected - Spoofing Blocked!", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.imshow("Face Capture", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        display_frame = cv2.convertScaleAbs(frame, alpha=1.2, beta=20)
        cv2.putText(display_frame, "Press 'c' to capture | 'q' to quit", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.imshow("Face Capture", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c'):
            print("📸 Attempting face capture...")
            while attempts < max_attempts:
                ret, frame = cap.read()
                if not ret:
                    continue
                embedding = extract_face_embedding(frame, fast_mode=False)
                if embedding is not None:
                    print("✅ Face captured successfully.")
                    cap.release()
                    cv2.destroyAllWindows()
                    return embedding
                attempts += 1
                print(f"[{attempts}/{max_attempts}] Retrying face detection...")

            print("❌ Failed to detect face. Try again with better lighting.")
            break

        elif key == ord('q'):
            print("❌ Capture cancelled.")
            break

        time.sleep(0.015)

    cap.release()
    cv2.destroyAllWindows()
    return None

def capture_and_store_face(email):
    embedding = capture_live_face_embedding()
    if embedding is None:
        return False
    os.makedirs("data/student_faces", exist_ok=True)
    with open(f"data/student_faces/{email}.pkl", "wb") as f:
        pickle.dump(embedding, f)
    print(f"💾 Face embedding saved for {email}")
    return True

def verify_face(email, threshold=0.5):
    embedding_path = f"data/student_faces/{email}.pkl"
    if not os.path.exists(embedding_path):
        print(f"❌ No saved embedding found for {email}")
        return False

    with open(embedding_path, "rb") as f:
        stored_embedding = pickle.load(f)

    live_embedding = capture_live_face_embedding()
    if live_embedding is None:
        print("❌ No face detected during live capture.")
        return False

    similarity = cosine_similarity([stored_embedding], [live_embedding])[0][0]
    print(f"🔍 Cosine similarity: {similarity:.2f}")
    return similarity >= threshold
