# FleetGuardian AI - Module 1 (CV & Foundation Infrastructure)

FleetGuardian AI is an enterprise-grade real-time fleet safety monitoring system. Module 1 establishes the clean, modular, and SOLID-compliant foundations for computer vision (CV) processing and repository utilities.

## Core Objectives
* **Modular Codebase**: Avoid monolithic script files. Break code into specialized classes and packages following the Single Responsibility Principle (SRP).
* **Enterprise Utilities**: Consolidate configuration loading, logging, execution timers, path parsing, and image/video manipulations into reusable modules.
* **Resilient Camera Ingest**: Stream frames from webcams, RTSP streams, IP cameras, or video files in a background thread to prevent lag.
* **YOLO & MediaPipe Wrappers**: Abstract the complexity of model loading, batch inference, bounding box extraction, and facial landmark math (EAR, MAR, asymmetry distraction).
* **Dataset Auditing**: Provide automatic verification tools to scan datasets for image corruption, duplicates, missing annotations, and split them safely.

## Documentation Index
1. **[Folder Explanation](folder_explanation.md)**: Detailed mapping of directories, submodules, and clean architecture boundaries.
2. **[Installation Guide](installation_guide.md)**: Environment setup, Python dependency installation, model file procurement, and unit test execution.
3. **[Usage Examples](usage_examples.md)**: Code recipes and snippets showing how to invoke the camera, image processors, YOLO wrapper, MediaPipe models, and dataset managers.
