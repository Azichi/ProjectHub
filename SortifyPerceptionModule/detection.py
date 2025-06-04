"""
detection.py

Handles HSV color masks, shape detection (circle/square/rectangle).
Raw 2D detection logic only.
"""

import cv2
import numpy as np
from typing import Protocol, Dict, Any, List
from config import TRACK_TARGETS
from preprocessing import clean_mask as morph
from preprocessing import apply_gaussian_blur
from position_estimation import mask_overlap as circle_mask_overlap


class Detector(Protocol):
    """
    Interface for any shape detector (circle, square).
    """    
    def detect(self, mask: np.ndarray, params: dict) -> List[dict]:
        results = [{"circularity_score": 0.92, "contour_area": 200.0, "bounding_box": [100, 120, 50, 50]}]
        return results


DETECTOR_REGISTRY: Dict[str, Detector] = {}


def register_detector(name: str, det: Detector):
    """
    Register a new shape detector (circle, square, etc.).
    """    
    if name and det:
        DETECTOR_REGISTRY[name] = det


class CircleDetector:
    """
    Detect circles in a given mask using HoughCircles.
    """    
    def detect(self, mask: np.ndarray, params: dict) -> List[Dict[str, Any]]:
        dp = float(params["dp"]) / 10.0
        minDist = int(params["minDist"])
        param1 = float(params["param1"])
        param2 = float(params["param2"])
        minRadius = int(params["minRadius"])
        maxRadius = int(params["maxRadius"])

        mask_overlap_thresh = float(params.get("c_mask_thr", 65)) / 100.0

        # Apply blur to smooth mask
        ksize = int(params.get("gaussian_k", 9))
        blurred = apply_gaussian_blur(mask, kernel_size=ksize)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp,
            minDist,
            param1=param1,
            param2=param2,
            minRadius=minRadius,
            maxRadius=maxRadius,
        )

        img_h, img_w = mask.shape[:2]
        raw: List[Dict[str, float]] = []

        if circles is None:
            return raw

        for cx, cy, r in np.round(circles[0]).astype(int):
            cx = np.clip(cx, 0, img_w - 1)
            cy = np.clip(cy, 0, img_h - 1)
            r = np.clip(r, 1, min(img_w, img_h) // 2)

            if mask[cy, cx] == 0:
                continue

            patch = mask[
                max(0, cy - r) : min(cy + r + 1, img_h),
                max(0, cx - r) : min(cx + r + 1, img_w),
            ]
            if cv2.countNonZero(patch) < int(params.get("c_area", 500)):
                continue

            circle_mask = np.zeros_like(mask)
            cv2.circle(circle_mask, (cx, cy), r, 255, -1)
            masked_blob = cv2.bitwise_and(mask, mask, mask=circle_mask)
            contours, _ = cv2.findContours(
                masked_blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            if not contours:
                continue
            cnt = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(cnt)
            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue
            circ = 4 * np.pi * area / (peri * peri)
            if circ < float(params.get("c_circ", 75)) / 100.0:
                continue

            if circle_mask_overlap(mask, cx, cy, r) < mask_overlap_thresh:
                continue

            det = {
                "cx": float(cx),
                "cy": float(cy),
                "r": float(r),
                "circularity_score": circ,
            }

            duplicate = False
            for prev in raw:
                dx = det["cx"] - prev["cx"]
                dy = det["cy"] - prev["cy"]
                dr = det["r"] - prev["r"]
                if dx * dx + dy * dy < (0.5 * det["r"]) ** 2 and abs(dr) < 10:
                    duplicate = True
                    break
            if not duplicate:
                raw.append(det)

        return raw


class SquareDetector:
    """
    Detect squares in a given mask by finding contours.
    """    
    def detect(self, mask: np.ndarray, p: dict) -> List[Dict[str, Any]]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = []
        eps_scale = p["s_eps"] / 1000.0

        for cnt in contours:
            if (
                len(cv2.approxPolyDP(cnt, eps_scale * cv2.arcLength(cnt, True), True))
                != 4
            ):
                continue

            area = cv2.contourArea(cnt)
            if not (p["s_min_area"] <= area <= p["s_max_area"]):
                continue
            hull_area = cv2.contourArea(cv2.convexHull(cnt))
            if (
                hull_area == 0
                or (area / hull_area) < p.get("s_sol", 80) / 100.0
            ):
                continue

            peri = cv2.arcLength(cnt, True)
            circ = 4 * np.pi * area / (peri * peri + 1e-6)
            if circ * 100 > p["s_circ"]:
                continue

            (cx, cy), (w, h), angle = cv2.minAreaRect(cnt)
            if w < h:
                w, h = h, w
                angle += 90.0
            angle %= 180.0
            if (area / (w * h)) < p.get("s_ext", 70) / 100.0:
                continue

            r = (w + h) / 4
            out.append({"cx": cx, "cy": cy, "r": r, "w": w, "h": h, "angle": angle})
        return out

# --- replace the old “FullRectangleDetector” block and its registration with this ---

class RectangleDetector:
    def detect(self, mask: np.ndarray, p: dict) -> List[Dict[str, Any]]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out = []

        eps_scale  = p["r_eps"] / 1000.0
        min_area   = p["r_min_area"]
        max_area   = p["r_max_area"]
        min_sol    = p.get("r_sol", 70) / 100.0
        min_extent = p.get("r_ext", 60) / 100.0
        circ_thr   = p["r_circ"]
        ar_min     = p["r_asp_min"] / 100.0
        ar_max     = p["r_asp_max"] / 100.0

        for cnt in contours:
            approx = cv2.approxPolyDP(cnt, eps_scale * cv2.arcLength(cnt, True), True)
            if len(approx) != 4:
                continue

            area = cv2.contourArea(approx)
            if not (min_area <= area <= max_area):
                continue

            hull_area = cv2.contourArea(cv2.convexHull(approx))
            if hull_area == 0 or (area / hull_area) < min_sol:
                continue

            (cx, cy), (w, h), angle = cv2.minAreaRect(approx)
            if w < h:
                w, h = h, w
                angle += 90.0
            angle %= 180.0
            if h == 0:
                continue

            aspect = w / h
            if not (ar_min <= aspect <= ar_max):
                continue

            if (area / (w * h)) < min_extent:
                continue

            peri = cv2.arcLength(approx, True)
            circ = 4 * np.pi * area / (peri * peri + 1e-6) * 100
            if circ > circ_thr:
                continue

            r = (w + h) / 4.0
            out.append({
                "cx": float(cx),
                "cy": float(cy),
                "r":  float(r),
                "w":  float(w),
                "h":  float(h),
                "angle": float(angle),
                "aspect_ratio": float(aspect),
                "area": float(area),
                "shape": "rectangle",
            })
        return out





class DetectColor:
    """
    Static methods to detect specific colors in HSV image.
    """    
    @staticmethod
    def red(hsv_img, p):
        lower1 = np.array([p["R1 H min"], p["R S min"], p["R V min"]])
        upper1 = np.array([p["R1 H max"], p["R S max"], p["R V max"]])
        lower2 = np.array([p["R2 H min"], p["R S min"], p["R V min"]])
        upper2 = np.array([p["R2 H max"], p["R S max"], p["R V max"]])
        mask1 = cv2.inRange(hsv_img, lower1, upper1)
        mask2 = cv2.inRange(hsv_img, lower2, upper2)
        return cv2.bitwise_or(mask1, mask2)

    @staticmethod
    def blue(hsv_img, p):
        lower = np.array([p["B H min"], p["B S min"], p["B V min"]])
        upper = np.array([p["B H max"], p["B S max"], p["B V max"]])
        return cv2.inRange(hsv_img, lower, upper)

    @staticmethod
    def green(hsv_img, p):
        l = (p["G H min"], p["G S min"], p["G V min"])
        u = (p["G H max"], p["G S max"], p["G V max"])
        return cv2.inRange(hsv_img, l, u)

    @staticmethod
    def yellow(hsv_img, p):
        l = (p["Y H min"], p["Y S min"], p["Y V min"])
        u = (p["Y H max"], p["Y S max"], p["Y V max"])
        return cv2.inRange(hsv_img, l, u)
    
    @staticmethod
    def neon_yellow(hsv: np.ndarray, params: dict) -> np.ndarray:
        lower = np.array([
            params["N H min"],
            params["N S min"],
            params["N V min"]
        ])
        upper = np.array([
            params["N H max"],
            params["N S max"],
            params["N V max"]
        ])
        return cv2.inRange(hsv, lower, upper)





def color_mask(hsv: np.ndarray, colour: str, params: dict) -> np.ndarray:
    """
    Get the color mask for a specified color from the HSV image.
    """
    func = getattr(DetectColor, colour, None)
    if func is None:
        return np.zeros_like(hsv[:, :, 0])
    try:
        return func(hsv, params)
    except Exception:
        return np.zeros_like(hsv[:, :, 0])


register_detector("circle", CircleDetector())
register_detector("square", SquareDetector())
register_detector("rectangle", RectangleDetector())



def detect_objects(frame_bgr: np.ndarray, params: dict) -> List[dict]:
    """
    Detect objects in a frame using color and shape detectors.
    """    
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    results = []
    for tgt in TRACK_TARGETS:
        shape = tgt["shape"]
        color = tgt["color"]
        mask = color_mask(hsv, color, params)
        mask = morph(mask, params)
        if mask is None or not isinstance(mask, np.ndarray) or mask.size == 0:
            continue
        for shp_data in detect_shape(mask, shape, params):
            results.append({"shape": shape, "color": color, "data": shp_data})
    return results


def detect_shape(mask: np.ndarray, shape: str, params: dict) -> List[dict]:
    """
    Detect a specific shape in a mask.
    """    
    det = DETECTOR_REGISTRY.get(shape)
    if det is None:
        return []
    return det.detect(mask, params)
