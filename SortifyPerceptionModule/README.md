# Sortify Perception Module

This Python module implements a vision pipeline used in the Sortify project. It relies on OpenCV and a small YOLO model to detect colored shapes and provide their positions.

## Requirements

Install dependencies with:

```bash
pip install -r requirements.txt
```

YOLO weights are included in `YOLO model/`. Example videos and images are provided for testing but add significant size to the repository.

## Running

The main entry point is `perception_controller.py`. It processes frames from a camera or video, runs detection and tracking, and can publish results over ROS 2 if `rclpy` is available.

```bash
python perception_controller.py
```

Adjust settings in `config.py` to enable/disable GUI controls, YOLO verification, or logging.
