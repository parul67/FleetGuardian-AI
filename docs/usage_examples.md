# Usage Examples & Recipes

This document provides snippets showing how to reuse individual submodules built during Module 1.

---

## 1. Configurations and Logging
Load the configurations and print log outputs:

```python
from utils import ConfigLoader, logger, Timer

# Load config using dot access (Singleton)
config = ConfigLoader()
width = config.get("camera.width", 640)
logger.info(f"Loaded camera width: {width}")

# Context Timer benchmark
with Timer("Sample Computation"):
    total = sum(i * i for i in range(100000))
```

---

## 2. Image Preprocessing
Normalize and equalize frames:

```python
import cv2
from cv.image_processing import ImagePreprocessor

# Load frame
frame = cv2.imread("driver.jpg")

# Preprocess: equalize light (CLAHE) + resize keeping aspect ratio + normalize
processed = ImagePreprocessor.preprocess_frame(
    frame,
    target_size=(640, 640),
    normalize=True,
    equalize=True
)
```

---

## 3. Camera Threaded Streaming
Capture video stream asynchronously (prevents UI blocking):

```python
import cv2
import time
from cv.camera import CameraStream

# Source can be 0 (webcam), a video path, or RTSP URL
with CameraStream(source=0, width=640, height=480, fps=30) as stream:
    # Let camera initialize
    time.sleep(1.0)
    
    while stream.running:
        ret, frame = stream.read()
        if not ret or frame is None:
            continue
            
        cv2.imshow("Live Stream", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
```

---

## 4. YOLO Object Detection Wrapper
Detect driver behaviors (like cell phone, smoking):

```python
from cv.yolo import YOLOWrapper
import cv2

# Initialize wrapper
yolo = YOLOWrapper()

# Load frame
frame = cv2.imread("cabin.jpg")

# Run inference
predictions = yolo.predict(frame)

# Draw results
annotated = yolo.draw_predictions(frame, predictions)
cv2.imwrite("cabin_annotated.jpg", annotated)
```

---

## 5. MediaPipe Face Mesh
Extract EAR, MAR, and distraction parameters:

```python
import cv2
from cv.mediapipe import FaceLandmarkerWrapper

# Initialize
face_mesh = FaceLandmarkerWrapper()

# Process
frame = cv2.imread("face.jpg")
face_data = face_mesh.process(frame)

if face_data:
    print(f"Eye Aspect Ratio (EAR): {face_data['ear']:.2f}")
    print(f"Mouth Aspect Ratio (MAR): {face_data['mar']:.2f}")
    print(f"Distraction score: {face_data['distraction_score']:.2f}")
```

---

## 6. Dataset Audit Utilities
Audit dataset directories for duplicates, corruptions, and missing labels:

```python
from datasets import DatasetManager

# Initialize manager
manager = DatasetManager("path/to/dataset")

# Verify structure
if manager.validate_structure():
    # Scan corrupted images
    corrupt = manager.scan_corrupted_images()
    
    # Scan duplicates
    duplicates = manager.scan_duplicate_images()
    
    # Split dataset (70% train, 20% val, 10% test)
    manager.train_val_test_split(
        output_dir="path/to/split_dataset",
        train_ratio=0.7,
        val_ratio=0.2,
        test_ratio=0.1
    )
```
