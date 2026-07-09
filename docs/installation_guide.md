# Installation and Setup Guide

## Requirements
* Python 3.12+ (tested on Python 3.12.10)
* C++ Build tools (required for compiling certain python packages like mediapipe)

## Initial Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd FleetGuardian-AI
   ```

2. **Initialize and Activate Virtual Environment**:
   * On Windows (PowerShell):
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   * On Linux/macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Model Downloads

FleetGuardian AI requires pre-trained model weights. 
* **YOLO Weights**: By default, `yolo11n.pt` is stored in the project root. If missing, it will automatically download upon first run.
* **MediaPipe Face Landmarker**: `face_landmarker.task` is located in the project root. If missing, the Face Mesh wrapper will download the float16 face landmarker file to the configured folder automatically.
  To download it manually:
  ```bash
  curl -o face_landmarker.task https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task
  ```

## Running Tests

Verify your environment configuration by executing the Pytest suite.
To prevent local temp folders permission issues, override the base temp directory:

```bash
# Set PYTHONPATH and run tests
$env:PYTHONPATH="."
.\venv\Scripts\pytest tests/ --basetemp=./tmp_pytest
```

All 21 test checks should complete successfully in under 3 seconds.
