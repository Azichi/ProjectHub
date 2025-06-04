"""
position_estimation.py

Converts 2D detection and depth map into 3D camera coordinates.
Includes camera-to-robot frame transformation and depth validation.
"""


from config import CAMERA_LEFT_MM, CAMERA_ABOVE_BASE_MM
from typing import Tuple, Optional, Dict
import cv2
import numpy as np
from config import (
    MASK_OVERLAP_OK,
    DEPTH_MIN_MM,
    DEPTH_MAX_MM,
    DEPTH_OFFSET_MM,
    #CAMERA_ABOVE_BASE_MM,
    #CAMERA_LEFT_MM
)
#from config import TILT_CORRECTION_DEGREES
import math

import numpy as np
import math
from typing import Tuple

# CAMERA SETTINGS — FILL IN BASED ON YOUR SETUP
CAMERA_LEFT_MM = 185.0           # how far camera is from robot center (left-right)
CAMERA_FORWARD_MM = 0.0          # how far camera is in front of robot base
CAMERA_ABOVE_BASE_MM = 195.0     # height of camera above robot base
TILT_DEGREES = 27.5             # camera tilt downward (negative = looking down)

def get_rotation_matrix_x(degrees: float) -> np.ndarray:
    angle = math.radians(degrees)
    return np.array([
        [1, 0, 0],
        [0, math.cos(angle), -math.sin(angle)],
        [0, math.sin(angle),  math.cos(angle)]
    ])

class PositionEstimator:
    @staticmethod
    def to_3d(
        u: float, v: float, z: float, fx: float, fy: float, cx: float, cy: float
    ) -> Tuple[float, float, float]:
        """
        Convert 2D pixel (u,v) and depth z into 3D coordinates in camera space.
        """
        x = (u - cx) * z / fx
        y = (v - cy) * z / fy
        return x, y, z

    @staticmethod
    def transform_camera_to_robot(x_mm: float, y_mm: float, z_mm: float) -> Tuple[float, float, float]:
        """
        Convert 3D point from camera coordinates to robot coordinates.
        """
        # Tilt correction (rotate point around x-axis)
        point = np.array([[x_mm], [y_mm], [z_mm]])
        R = get_rotation_matrix_x(TILT_DEGREES)
        point_rotated = R @ point

        # Apply camera offset relative to robot
        x_r = point_rotated[0, 0] + CAMERA_LEFT_MM
        y_r = point_rotated[1, 0] + CAMERA_FORWARD_MM
        z_r = CAMERA_ABOVE_BASE_MM - point_rotated[2, 0]

        return x_r, y_r, z_r









    @staticmethod
    def mask_overlap(mask: np.ndarray, cx: int, cy: int, r: int) -> float:
        """
        Calculate the overlap between a circular mask and a region of interest in the mask.
        """        
        if r <= 0:
            return 0.0
        h, w = mask.shape[:2]
        circ = np.zeros((h, w), dtype=np.uint8)
        cv2.circle(circ, (cx, cy), r, 255, -1)
        overlap = cv2.bitwise_and(mask, circ)
        area_circ = cv2.countNonZero(circ)
        area_inter = cv2.countNonZero(overlap)
        return (area_inter / area_circ) if area_circ else 0.0

    @staticmethod
    def estimate_position(
        det: Dict,
        depth_map: np.ndarray,
        fx: float,
        fy: float,
        cx0: float,
        cy0: float,
        mask: Optional[np.ndarray] = None,
    ) -> Dict:
        """
        Estimate the 3D position of an object based on its 2D coordinates and the depth map.
        Also checks for depth validity and mask overlap.
        """        

        if not det or any(k not in det for k in ("cx", "cy", "r")):
            return PositionEstimator.empty_result()

        cx, cy, r = map(int, map(round, (det["cx"], det["cy"], det["r"])))
        h, w = depth_map.shape
        if not (0 <= cx < w and 0 <= cy < h) or r <= 3:
            return PositionEstimator.empty_result()

        roi = np.zeros_like(depth_map, dtype=np.uint8)
        cv2.circle(roi, (cx, cy), r, 255, -1)
        if mask is not None:
            roi = cv2.bitwise_and(roi, mask.astype(np.uint8))

        valid_depth = (depth_map >= DEPTH_MIN_MM) & (depth_map <= DEPTH_MAX_MM)
        depth_vals = depth_map[(roi > 0) & valid_depth]
        if depth_vals.size < 20:
            return PositionEstimator.empty_result()

        med = float(np.median(depth_vals))
        mad = float(np.median(np.abs(depth_vals - med))) or 1.0

        if depth_vals.size < 15:
            return PositionEstimator.empty_result()

        z_mm = float(np.median(depth_vals)) + DEPTH_OFFSET_MM

        m = cv2.moments(roi, binaryImage=True)
        if m["m00"] == 0:
            return PositionEstimator.empty_result()
        u = m["m10"] / m["m00"]
        v = m["m01"] / m["m00"]

        x_mm, y_mm, z_mm = PositionEstimator.to_3d(u, v, z_mm, fx, fy, cx0, cy0)

        overlap = PositionEstimator.mask_overlap(mask if mask is not None else roi, cx, cy, r)

        return {
            "x_mm": x_mm,
            "y_mm": y_mm,
            "z_mm": z_mm,
            "depth_valid": DEPTH_MIN_MM <= z_mm <= DEPTH_MAX_MM,
            "depth_mask_valid": overlap >= MASK_OVERLAP_OK,
        }

    @staticmethod
    def empty_result() -> Dict:
        """
        Return an empty result with invalid depth and mask data.
        """        
        return {
            "x_mm": 0.0,
            "y_mm": 0.0,
            "z_mm": 0.0,
            "depth_valid": False,
            "depth_mask_valid": False,
        }

# Shortcuts
estimate_position = PositionEstimator.estimate_position
to_3d             = PositionEstimator.to_3d
mask_overlap      = PositionEstimator.mask_overlap
transform_camera_to_robot = PositionEstimator.transform_camera_to_robot
