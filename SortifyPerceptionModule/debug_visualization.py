"""
debug_visualization.py

Draws detection overlays and assembles debug view for live testing.
Handles per-object drawing and builds composite 2x2 debug window.
No preprocessing or detection logic implemented here.
"""


from typing import List, Dict, Any
import cv2
import numpy as np
from config import COLOR_BGR

def draw_detections(img: np.ndarray, detections: List[Dict[str, Any]]) -> None:
    for det in detections:
        color_str = det.get("color", "").capitalize()
        shape_str = det.get("shape", "").lower()
        color = COLOR_BGR.get(det.get("color", "").lower(), (200, 200, 200))
        d = det.get("data", det)

        cx, cy = int(round(d.get("cx", 0))), int(round(d.get("cy", 0)))
        label = f"{color_str} {shape_str} - ID: {d.get('track_id', '?')}"

        if shape_str == "circle":
            r = int(round(d.get("r", 0)))
            if r > 0:
                        cv2.circle(img, (cx, cy), r, color, 2)
        elif shape_str in ("square", "rectangle"):
            if all(k in d for k in ("w", "h", "angle")):
                rect = ((cx, cy), (d["w"], d["h"]), d.get("angle", 0.0))
                box = cv2.boxPoints(rect).astype(int)
                cv2.drawContours(img, [box], -1, color, 2)




        # Draw label in white
        cv2.putText(
            img, label, (cx - 100, cy - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
        )

        if all(k in d for k in ("x_mm", "y_mm", "z_mm")):
            xyz = f"X: {d['x_mm']:.0f}  Y: {d['y_mm']:.0f}  Z: {d['z_mm']:.0f}"
            cv2.putText(
                img,
                xyz,
                (cx - 100, cy - 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

def draw_scoring_overlay(img: np.ndarray, detections: List[Dict[str, Any]]) -> None:
    """
    Draws a frosty, ultra-white, futuristic scoring overlay to the LEFT of each detected object.
    """
    for det in detections:
        d = det.get("data", det)
        cx, cy = int(d.get("cx", 0)), int(d.get("cy", 0))
        r = int(d.get("r", 0))

        # Scoring breakdown
        checks = [
            ("HSV", d.get("color_valid", False)),
            ("Shape", d.get("shape_valid", False)),
            ("AI", d.get("ai_valid", False)),
            ("Depth", d.get("depth_valid", False)),
            ("Mask", d.get("depth_mask_valid", False)),
            ("Track", d.get("tracker_valid", False)),
        ]
        accepted = d.get("accepted", False)

        # Overlay box position — LEFT of the object
        box_w = 195
        box_h = (len(checks) + 2) * 28  # extra line height for spacing
        padding = 7
        font = cv2.FONT_HERSHEY_SIMPLEX
        box_x = cx - r - box_w - 18
        box_y = cy - 20

        # Draw **solid white with high alpha** (true "frosted glass" effect)
        overlay = img.copy()
        cv2.rectangle(overlay, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), -1)
        alpha = 0.85  # High alpha for stronger white; lower if you want more see-through
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        # White outline
        cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 255, 255), 3)

        # Draw all text in pure white except specific fails/results
        for i, (label, ok) in enumerate(checks):
            # Red for any fail, otherwise pure white
            txt_color = (40, 40, 40) if ok else (0, 0, 255)
            text = f"{label:<7}: {'Pass' if ok else 'Fail'}"
            y = box_y + padding + (i + 1) * 28
            cv2.putText(img, text, (box_x + padding, y), font, 0.65, txt_color, 2, cv2.LINE_AA)

        # Result line: bright green for accepted, hot red for rejected
        result_txt = f"Result : {'Accepted' if accepted else 'Rejected'}"
        result_color = (90, 235, 170) if accepted else (255, 60, 80)
        final_y = box_y + padding + (len(checks) + 1) * 28
        cv2.putText(img, result_txt, (box_x + padding, final_y), font, 0.65, result_color, 3, cv2.LINE_AA)





# Create composite debug view (2×2)
def build_debug_view(
    preproc: np.ndarray,           
    red_mask: np.ndarray,
    blue_mask: np.ndarray,
    overlay: np.ndarray,
) -> np.ndarray:

    h, w = preproc.shape[:2]

    def to_bgr(img: np.ndarray) -> np.ndarray:
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return cv2.resize(img, (w, h))


    pane0   = to_bgr(preproc)
    red_bgr = to_bgr(red_mask)
    blue_bgr= to_bgr(blue_mask)
    overlay = to_bgr(overlay)

    top    = np.hstack((pane0,   red_bgr))
    bottom = np.hstack((blue_bgr, overlay))

    
    return np.vstack((top, bottom))
