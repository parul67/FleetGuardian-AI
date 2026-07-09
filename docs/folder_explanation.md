# Directory and Architecture Structure

FleetGuardian AI Module 1 uses a decoupled, clean architecture to ensure maintainability, testing scalability, and future integration by backend APIs.

```text
FleetGuardian-AI/
├── configs/
│   └── config.yaml               # Consolidated settings (resolutions, thresholds, paths)
├── cv/
│   ├── __init__.py               # Top-level exports
│   ├── camera/
│   │   ├── __init__.py
│   │   └── camera_stream.py      # Threaded ingestion (Webcam, RTSP, IP, Files)
│   ├── image_processing/
│   │   ├── __init__.py
│   │   └── preprocessor.py       # Basic operations (resize, crop, equalize, CLAHE)
│   ├── mediapipe/
│   │   ├── __init__.py
│   │   └── mediapipe_wrapper.py  # Face Mesh (EAR/MAR), Pose, and Hands wrappers
│   ├── video_processing/
│   │   ├── __init__.py
│   │   └── video_io.py           # Buffers, writers, readers, and properties
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── renderer.py           # HUD overlay renderer and banner warnings
│   └── yolo/
│       ├── __init__.py
│       └── yolo_wrapper.py       # Decoupled YOLO wrapper for inference
├── datasets/
│   ├── __init__.py
│   └── dataset_manager.py        # Duplication, corruption, validation, splits
├── docs/
│   ├── README.md
│   ├── folder_explanation.md
│   ├── installation_guide.md
│   └── usage_examples.md
├── models/                       # Folder for model weights
├── pipelines/
│   ├── __init__.py
│   └── safety_pipeline.py        # Safety aggregate executing CV submodules
├── scripts/
│   └── run_pipeline.py           # CLI pipeline demonstration script
├── tests/
│   ├── test_config.py
│   ├── test_dataset_manager.py
│   ├── test_image_processing.py
│   └── test_utils.py
└── utils/
    ├── __init__.py
    ├── config_loader.py          # Singleton dot-notation config parser
    ├── file_manager.py           # Directory/file helpers
    ├── fps_calculator.py         # Rolling window FPS tracker
    ├── image_helper.py           # Loading, saving, and base64 parsing
    ├── logger.py                 # console & rotating file logger
    ├── path_utils.py             # absolute-safe path translations
    ├── seed_initializer.py       # reproducibility state
    ├── timer.py                  # speed timings (context & decorator)
    └── video_helper.py           # video properties reader
```

## SOLID & Clean Architecture Compliance

* **Single Responsibility Principle (SRP)**: Each class has a single purpose. `CameraStream` only captures frames, `YOLOWrapper` only manages object predictions, `CanvasRenderer` only handles image overlays, and `DatasetManager` only manages dataset checks.
* **Open/Closed Principle (OCP)**: Visualization methods are written as extendable static methods. Additional overlays can be added to `CanvasRenderer` without rewriting existing bounding box methods.
* **Liskov Substitution Principle (LSP)**: Video extraction classes implement standard generator protocols, allowing them to be swapped.
* **Interface Segregation Principle (ISP)**: Configuration loader and file manager provide granular sub-utilities so modules only consume what they require.
* **Dependency Inversion Principle (DIP)**: Low-level file I/O operations are abstracted out of core models. Models load paths resolved by `PathUtils` rather than hardcoding local references.
