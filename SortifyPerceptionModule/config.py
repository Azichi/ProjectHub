"""
config.py

Global parameters and all system settings for detection, tracking, color, and GUI.
"""

from typing import Dict, Tuple, Any
import logging

# Mode, enabling GUI, sliders, YOLO + other settings
MODE = "demo"        # safety - sortify - demo
USE_GUI: bool = True
USE_TRACKBARS: bool = True
ENABLE_YOLO: bool = True
DRAW_DETECTIONS = True
DRAW_SCORING = False
DEBUG_LAYOUT = "2x1"  # "2x1" or "2x2"



# Which shapes/colors are tracked in this system
TRACK_TARGETS = [
    {"shape": "circle", "color": "red"},
    {"shape": "circle", "color": "blue"},
    #{"shape": "circle", "color": "green"},
    #{"shape": "square", "color": "red"},
    #{"shape": "square", "color": "green"},
    #{"shape": "square", "color": "blue"},
    #{"shape": "rectangle", "color": "neon_yellow"},

]

# BGR color codes for overlays and drawing
COLOR_BGR: Dict[str, Tuple[int, int, int]] = {
    "red": (0, 0, 255),
    "blue": (255, 0, 0),
    "green": (0, 255, 0),
    "yellow": (0, 255, 255),
    "neon_yellow": (0, 255, 200),
}

# Offset/tilt correction for position estimation
TILT_DEGREES = 0
CAMERA_LEFT_MM = 0
CAMERA_ABOVE_BASE_MM  = 0
CAMERA_FORAWRD_MM = 0

# Depth and position estimation
MASK_OVERLAP_OK: float = 0.65
Z_CORRECTION_BY_ROW = {"top": 0.0, "middle": 0.0, "bottom": 0.0}
DEPTH_MIN_MM: int = 500
DEPTH_MAX_MM: int = 1000
DEPTH_OFFSET_MM = 0

# DEPTHAI camera settings
CAMERA_WIDTH: int = 640
CAMERA_HEIGHT: int = 400
CAMERA_FPS: int = 60
CAMERA_STILL_SIZE: Tuple[int, int] = (1920, 1080)
CAMERA_DEPTH_RESOLUTION: str = "THE_800_P"
CAMERA_CONFIDENCE_THRESHOLD: int = 200
CAMERA_MEDIAN_FILTER: str = "KERNEL_5x5"
CAMERA_STEREO_ALIGNMENT: str = "RGB"

# Live GUI sliders
TRACKBAR_WINDOW: str = "Trackbars"
TRACKBAR_MAX: int = 255

# Which slider groups are enabled
ACTIVE_GROUPS = [
    "circle",
    #"square",
    #"rectangle",
    "hsv_red",
    "hsv_blue",
    #"hsv_green",
    #"hsv_neon_yellow",
    "morphology",
    "tracking",
    #"camera",
    "kalman",
    "preprocessing",
    "evaluation",
]

# Slider/trackbar configuration
SLIDER_CONFIG: Dict[str, Dict[str, Any]] = {
    # Red HSV Range
    "R1 H min": {"default": 0, "max": 20, "group": "hsv_red"},
    "R1 H max": {"default": 9, "max": 180, "group": "hsv_red"},
    "R2 H min": {"default": 170, "max": 180, "group": "hsv_red"},
    "R2 H max": {"default": 180, "max": 180, "group": "hsv_red"},
    "R S min": {"default": 200, "max": 255, "group": "hsv_red"},
    "R S max": {"default": 255, "max": 255, "group": "hsv_red"},
    "R V min": {"default": 25, "max": 255, "group": "hsv_red"},
    "R V max": {"default": 255, "max": 255, "group": "hsv_red"},
    # Blue HSV Range
    "B H min": {"default": 105, "max": 180, "group": "hsv_blue"},
    "B H max": {"default": 145, "max": 180, "group": "hsv_blue"},
    "B S min": {"default": 100, "max": 255, "group": "hsv_blue"},
    "B S max": {"default": 255, "max": 255, "group": "hsv_blue"},
    "B V min": {"default": 50, "max": 205, "group": "hsv_blue"},
    "B V max": {"default": 255, "max": 255, "group": "hsv_blue"},
    # Green HSV Range
    "G H min": {"default": 23, "max": 180, "group": "hsv_green"},
    "G H max": {"default": 90, "max": 180, "group": "hsv_green"},
    "G S min": {"default": 80, "max": 255, "group": "hsv_green"},
    "G S max": {"default": 255, "max": 255, "group": "hsv_green"},
    "G V min": {"default": 25, "max": 205, "group": "hsv_green"},
    "G V max": {"default": 255, "max": 255, "group": "hsv_green"},
    # Yellow HSV Range
    "Y H min": {"default": 20, "max": 35, "group": "hsv_yellow"},
    "Y H max": {"default": 35, "max": 80, "group": "hsv_yellow"},
    "Y S min": {"default": 100, "max": 255, "group": "hsv_yellow"},
    "Y S max": {"default": 255, "max": 255, "group": "hsv_yellow"},
    "Y V min": {"default": 100, "max": 255, "group": "hsv_yellow"},
    "Y V max": {"default": 255, "max": 255, "group": "hsv_yellow"},
    # Neon Yellow HSV Range
    "N H min": {"default": 12, "max": 40, "group": "hsv_neon_yellow"},
    "N H max": {"default": 60, "max": 80, "group": "hsv_neon_yellow"},
    "N S min": {"default": 105, "max": 255, "group": "hsv_neon_yellow"},
    "N S max": {"default": 255, "max": 255, "group": "hsv_neon_yellow"},
    "N V min": {"default": 80, "max": 255, "group": "hsv_neon_yellow"},
    "N V max": {"default": 255, "max": 255, "group": "hsv_neon_yellow"},
    # Morphology
    "kernel_size": {"default": 0, "max": 31, "group": "morphology"},
    "open_iter": {"default": 0, "max": 10, "group": "morphology"},
    "close_iter": {"default": 0, "max": 20, "group": "morphology"},
    # Circle Detection
    "dp": {"default": 20, "max": 30, "group": "circle"},
    "minDist": {"default": 200, "max": 200, "group": "circle"},
    "param1": {"default": 200, "max": 255, "group": "circle"},
    "param2": {"default": 60, "max": 255, "group": "circle"},
    "minRadius": {"default": 50, "max": 200, "group": "circle"},
    "maxRadius": {"default": 200, "max": 200, "group": "circle"},
    "c_area": {"default": 2500, "max": 10000, "group": "circle"},
    "c_mask_thr": {"default": 70, "max": 100, "group": "circle"},
    "c_circ": {"default": 30, "max": 100, "group": "circle"},
    "c_iou_thr": {"default": 70, "max": 100, "group": "circle"},
    # Square Detection
    "s_sol": {"default": 30, "max": 100, "group": "square"},
    "s_ext": {"default": 85, "max": 100, "group": "square"},
    "s_min_area": {"default": 5000, "max": 50000, "group": "square"},
    "s_max_area": {"default": 80000, "max": 100000, "group": "square"},
    "s_eps": {"default": 100, "max": 500, "group": "square"},
    "s_asp_min": {"default": 60, "max": 100, "group": "square"},
    "s_asp_max": {"default": 110, "max": 150, "group": "square"},
    "s_circ": {"default": 97, "max": 100, "group": "square"},
    "s_iou_thr": {"default": 60, "max": 100, "group": "square"},
    # Rectangle Detection
    "r_min_area":  {"default": 50,   "max": 10000,  "group": "rectangle"},
    "r_max_area":  {"default": 500000, "max": 750000, "group": "rectangle"},
    "r_asp_min":   {"default": 50,     "max": 300,    "group": "rectangle"},  # aspect-ratio min (%)
    "r_asp_max":   {"default": 400,    "max": 3000,    "group": "rectangle"},  # aspect-ratio max (%)
    "r_eps":       {"default": 100,     "max": 200,     "group": "rectangle"},  # ε for approxPolyDP
    "r_sol":       {"default": 0,     "max": 200,    "group": "rectangle"},  # solidity threshold (%)
    "r_ext":       {"default": 50,     "max": 200,    "group": "rectangle"},  # extent threshold (%)
    "r_circ":      {"default": 200,    "max": 200,    "group": "rectangle"},  # circularity max (%)
    "r_rect_thresh": {"default": 10,   "max": 100,    "group": "rectangle"},  # rectangularity threshold (%)
    # Weights
    "Color Weight": {"default": 50, "max": 100, "group": "evaluation"},
    "Shape Weight": {"default": 50, "max": 100, "group": "evaluation"},
    "AI Weight": {"default": 100, "max": 100, "group": "evaluation"},
    "Depth Weight": {"default": 15, "max": 100, "group": "evaluation"},
    "Depth Mask Weight": {"default": 45, "max": 100, "group": "evaluation"},
    "Tracker Weight": {"default": 100, "max": 100, "group": "evaluation"},
    "Decision Accept Threshold": {"default": 200, "max": 390, "group": "evaluation"},
    # focus and Tracking
    "focus": {"default": 140, "max": 200, "group": "camera"},
    "tr_alpha": {"default": 20, "max": 100, "group": "tracking"},
    "match_dist": {"default": 1500, "max": 5000, "group": "tracking"},
    "max_lost": {"default": 30, "max": 30, "group": "tracking"},
    "spawn_persist": {"default": 0, "max": 30, "group": "tracking"},
    "speed_gain": {"default": 0, "max": 30, "group": "tracking"},
    "stable_age": {"default": 0, "max": 30, "group": "tracking"},
    "kf_q_2d": {"default": 2, "max": 50, "group": "kalman"},
    "kf_r_2d": {"default": 5, "max": 50, "group": "kalman"},
    "kf_q_3d": {"default": 10, "max": 50, "group": "kalman"},
    "kf_r_3d": {"default": 9, "max": 100, "group": "kalman"},
    # preprocessing
    "clahe_clip": {"default": 0, "max": 31, "group": "preprocessing"},
    "gaussian_k": {"default": 5, "max": 31, "group": "preprocessing"},
    "gaussian_sigma": {"default": 0, "max": 100, "group": "preprocessing"},
    "gray": {"default": 1, "max": 1, "group": "preprocessing"},
}


# YOLO AI model filepaths
YOLO_CFG: str = "/Users/azi/Desktop/Sortify/darknet/cfg/yolov4-tiny-6obj.cfg"
YOLO_WEIGHTS: str = "/Users/azi/Desktop/Sortify/darknet/backup/yolov4-tiny-6obj_last.weights"
YOLO_DATA: str = "/Users/azi/Desktop/Sortify/darknet/data/obj.data"


# Hardcoded ground truth positions (for test/metrics)
GROUND_TRUTH_POS: Dict[Tuple[str, str], Tuple[float, float, float]] = {
    ("circle", "red"): (-139.0, 34.5, 752.0),
    ("circle", "blue"): (140.2, 34, 751.0),
    ("square", "red"):  (0.0, 0.0, 500.0),
    ("square", "blue"): (0.0, 0.0, 500.0),
}

# Logging/KPI settings
LOG_COLUMNS = [
    "test_type", "frame", "time_sec", "fps", "track_id", "shape", "color",
    "x_mm", "y_mm", "z_mm", "pos_error_mm", "depth_valid", "depth_mask_valid",
    "color_valid", "shape_valid"
]
LOGGING_MAX_FRAMES_DEFAULT: int = 1000
LOGGING_TOGGLE_KEY: int = ord("l")
LOGGING_OUTPUT_DIR: str = "/Users/azi/Desktop/Sortify/PI Code/tests"
POS_ERROR_THRESHOLD_MM: float = 50.0
MAX_ERROR_SNAPSHOTS: int = 3

# Set up logging
LOG = logging.getLogger("sortify")
if not LOG.handlers:
    LOG.addHandler(logging.StreamHandler())
LOG.setLevel(logging.INFO)