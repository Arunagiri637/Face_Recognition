# Face Recognition Capture

A simple offline face-recognition capture tool that reads frames from a webcam, detects faces (Haar Cascade), computes face encodings with face_recognition (dlib), matches against a folder of known people, saves captured images to per-person folders, logs events to a text file and inserts capture records into a PostgreSQL table.

## Table of contents

Features

Requirements

Why Python 3.8?

Project layout

Installation (Quickstart)

Configuration

Database setup

How to run

Behavior & outputs

Naming convention for known faces

Troubleshooting & common errors

Performance tuning tips

Security & privacy

Optional extras you can add

License & Contact

## Features

Real-time webcam capture (OpenCV)

Face detection with Haar cascade

Face encoding and recognition using face_recognition (dlib)

Stores a copy of each captured face under captured_faces/<name>/

Simple append-only capture_log.txt for human-readable history

Inserts a record into local PostgreSQL table face_captures

Console feedback and simple on-frame annotation

## Requirements

Python: 3.8 (see below why)

### Libraries:

opencv-python

face_recognition (depends on dlib)

numpy

psycopg2-binary

You can install dependencies with a requirements.txt (example provided in the repo) or run:

pip install face_recognition opencv-python numpy psycopg2-binary

On Windows, installing dlib from source is difficult — prefer to install a prebuilt wheel for the matching Python version (3.8) or use conda.

### Why Python 3.8?

Many prebuilt dlib and face_recognition wheels are published for Python 3.8 and Windows users typically encounter fewer compatibility and build errors with that version. Using 3.8 reduces friction when installing dlib (which can otherwise require Visual Studio build tools) and helps ensure stable behavior with the installed OpenCV and psycopg2 binaries.

If you prefer, you can run on newer Python versions but be prepared to build dlib from source or locate a wheel compatible with your Python version and OS.


### Installation (Quickstart)

1, Clone repository.

2, Create and activate a virtual environment:

python -m venv .venv
#### Windows
.venv\Scripts\activate
#### macOS / Linux
source .venv/bin/activate

3, Install dependencies:
pip install -r requirements.txt
#### or
pip install face_recognition opencv-python numpy psycopg2-binary

4, Place haarcascade_frontalface_default.xml in the project root (it is included in OpenCV's repo if you need it).

5, Create or update the known_faces/ folder with sample images named with each person’s name (see naming section).

6, Create the PostgreSQL database/table (see Database setup).

## Configuration

Edit the top of fr_script.py to match your environment. Example variables to change:
known_faces_dir = r'C:\Users\PCM\PycharmProjects\FR\known_faces'
captured_faces_dir = r'C:\Users\PCM\PycharmProjects\FR\captured_faces'
haar_cascade_path = r'C:\Users\PCM\PycharmProjects\FR\haarcascade_frontalface_default.xml'
log_file = r'C:\Users\PCM\PycharmProjects\FR\capture_log.txt'

## PostgreSQL
conn = psycopg2.connect(
    dbname="face_recognition",
    user="postgres",
    password="your_pw",
    host="localhost",
    port="5432"
)

--Database setup--

Run the following SQL (or use the included init_db.sql) to create the DB and table:
CREATE DATABASE face_recognition;
\c face_recognition;

CREATE TABLE IF NOT EXISTS face_captures (
  id SERIAL PRIMARY KEY,
  image_name TEXT NOT NULL,
  capture_time TIMESTAMP NOT NULL,
  status TEXT NOT NULL
);

If PostgreSQL is on another host or uses different credentials, update the connection block in fr_script.py.

### How to run

With venv active and dependencies installed, run:

### Controls:

Press q to quit

Closing the video window also stops the script

Expected console outputs include connection success/failure messages, capture notifications and any DB errors.

### Behavior & outputs

On first run, captured_faces/ is created automatically.

For each detected face a cropped image is saved to captured_faces/<name>/<name>_<n>.jpg.

A line is appended to capture_log.txt with timestamp, file path and status.

A DB row is inserted into face_captures with image_name, capture_time, and status (Known or Unknown).

### Naming convention for known faces

Filenames in known_faces/ should be the person's name (no spaces ideally): Alice.jpg, bob.png.

The script extracts the base filename (without extension) as the person name used for saving captured images and DB records.

### Troubleshooting & common errors

Cannot open webcam: try different index cv2.VideoCapture(1) or check camera permissions. Ensure no other app is using the camera.

Haar cascade not loaded: confirm haar_cascade_path points to an existing haarcascade_frontalface_default.xml file.

face_recognition import or dlib build fails: on Windows, install a compatible prebuilt dlib wheel for Python 3.8 or use conda. See dlib GitHub for build instructions.

PostgreSQL connection failure: ensure service is running, port and credentials correct. Test with psql or a DB GUI.

No faces found in known image: the image might be too small, rotated, or have no detectable frontal face. Use clear frontal photos for the known_faces set.

Too many false positives / false negatives: tune cascade scaleFactor, minNeighbors, or use a better detector (HOG/CNN provided by face_recognition).

If the script crashes, read stack trace printed to console — traceback.print_exc() is already in place for DB inserts and will help locate issues.

### Performance tuning tips

Convert frames to smaller size before detection for higher FPS (but be careful with recognition accuracy).

Increase minNeighbors or minSize to reduce small false detections.

Use face_recognition's HOG or CNN detector on full frames (slower but often more accurate) instead of Haar cascade.

Use batch encoding: maintaining encodings in memory (already implemented) is much faster than re-encoding known faces repeatedly.

### Security & privacy

Captured face images are personal data. Make sure you have consent to capture and store faces.

If deploying in a real environment, consider encryption at rest, secure DB credentials, and access control.

Add a configuration switch to disable DB inserts or enable pseudonymization for demo/testing.

### Optional extras you can add

requirements.txt and Pipfile/environment.yml

init_db.sql and a small create_db.py helper script

CLI args or a config file to avoid editing source paths

Dockerfile for consistent environment

Unit tests for helper functions

A web UI to view captures and DB records

