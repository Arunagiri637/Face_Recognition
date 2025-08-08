import cv2
import face_recognition
import os
import numpy as np
import datetime
import psycopg2
import traceback

# Define paths
known_faces_dir = r'C:\Users\PCM\PycharmProjects\FR\known_faces'
captured_faces_dir = r'C:\Users\PCM\PycharmProjects\FR\captured_faces'
haar_cascade_path = r'C:\Users\PCM\PycharmProjects\FR\haarcascade_frontalface_default.xml'
log_file = r'C:\Users\PCM\PycharmProjects\FR\capture_log.txt'

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(
        dbname="face_recognition",
        user="postgres",
        password="arun",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    print("✅ Connected to PostgreSQL")
except Exception as e:
    print(f"❌ Error connecting to PostgreSQL: {e}")
    exit()

# Ensure the face_captures table exists
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS face_captures (
            id SERIAL PRIMARY KEY,
            image_name TEXT NOT NULL,
            capture_time TIMESTAMP NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    print("✅ Table 'face_captures' is ready.")
except Exception as e:
    print(f"❌ Error creating table: {e}")
    conn.close()
    exit()

# Load known faces
known_face_encodings = []
known_face_names = []

for filename in os.listdir(known_faces_dir):
    if filename.endswith(('.jpg', '.png')):
        image_path = os.path.join(known_faces_dir, filename)
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        if encodings:
            known_face_encodings.append(encodings[0])
            known_face_names.append(os.path.splitext(filename)[0])
        else:
            print(f"⚠️ No face found in {filename}")

# Create captured_faces directory if it doesn't exist
os.makedirs(captured_faces_dir, exist_ok=True)

# Start webcam
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    print("❌ Error: Could not open webcam.")
    cursor.close()
    conn.close()
    exit()

# Load Haar Cascade
face_cascade = cv2.CascadeClassifier(haar_cascade_path)
if face_cascade.empty():
    print("❌ Error: Could not load Haar Cascade file.")
    cursor.close()
    conn.close()
    exit()

cv2.namedWindow('Video', cv2.WINDOW_NORMAL)

last_capture_time = 0
capture_cooldown = 1  # seconds

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("❌ Error: Failed to capture frame.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=3, minSize=(20, 20))
    current_time = datetime.datetime.now().timestamp()

    for (x, y, w, h) in faces:
        face_image = frame[y:y+h, x:x+w]
        rgb_face = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)

        print("🔍 Extracting face encodings...")
        encodings = face_recognition.face_encodings(rgb_face)
        print(f"🧠 Found {len(encodings)} face(s).")

        name = "Unknown"

        if encodings and (current_time - last_capture_time) > capture_cooldown:
            encoding = encodings[0]
            face_distances = face_recognition.face_distance(known_face_encodings, encoding)
            matches = face_recognition.compare_faces(known_face_encodings, encoding)

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]

            person_dir = os.path.join(captured_faces_dir, name)
            os.makedirs(person_dir, exist_ok=True)

            filename = f"{name}_{len(os.listdir(person_dir))}.jpg"
            filepath = os.path.join(person_dir, filename)
            cv2.imwrite(filepath, face_image)

            last_capture_time = current_time
            status = "Known" if name != "Unknown" else "Unknown"

            print(f"📷 Face captured: {name}, saved as {filepath}, status: {status}")

            with open(log_file, 'a') as f:
                f.write(f"{datetime.datetime.now()}: Captured {name}, saved as {filepath}, status: {status}\n")

            # Database insertion
            print(f"📥 Attempting to insert record into DB for {name}...")
            try:
                cursor.execute(
                    "INSERT INTO face_captures (image_name, capture_time, status) VALUES (%s, %s, %s)",
                    (filename, datetime.datetime.now(), status)
                )
                conn.commit()
                print("✅ Record inserted successfully.")
            except Exception as e:
                print(f"❌ Error inserting into PostgreSQL: {e}")
                traceback.print_exc()
                conn.rollback()

            # On-screen feedback
            cv2.putText(frame, f"Captured: {name} ({status})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        # Draw face box and label
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(frame, name, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

    cv2.imshow('Video', frame)

    key = cv2.waitKey(10) & 0xFF
    if key == ord('q'):
        print("🛑 Q key pressed, exiting loop.")
        break
    if cv2.getWindowProperty('Video', cv2.WND_PROP_VISIBLE) < 1:
        print("🛑 Window closed, exiting loop.")
        break

# Cleanup
print("🧹 Releasing video capture and closing windows.")
video_capture.release()
cv2.destroyAllWindows()
cursor.close()
conn.close()
print("🔌 PostgreSQL connection closed.")
