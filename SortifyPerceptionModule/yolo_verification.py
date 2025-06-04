"""
yolo_verification.py
Handles YOLO object detection. Optionally used if ENABLE_YOLO is True.
Supports both OpenCV DNN (Darknet/ONNX).
"""
from pathlib import Path
from typing import List, Dict

import cv2
import numpy as np
from config import YOLO_CFG, YOLO_WEIGHTS

FRAME_COUNTER = 0

try:
    from rclpy.logging import get_logger
    log = get_logger("yolo_verification")
except Exception:  # pragma: no cover
    class Dummy:
        def debug(self, m): print("[DEBUG]", m)
        def info(self, m): print("[INFO ]", m)
        def warning(self, m): print("[WARN ]", m)
        def error(self, m): print("[ERROR]", m)
    log = Dummy()

model_handle = None
class_name_map: Dict[int, str] = {}
MODEL_SIDE = 416


def load_model_once() -> None:
    """
    Load YOLO weights with OpenCV DNN.
    """
    global model_handle, class_name_map
    if model_handle is not None:
        return
    w_path, c_path = Path(YOLO_WEIGHTS).expanduser(), Path(YOLO_CFG).expanduser()
    if not w_path.exists():
        raise FileNotFoundError(f"YOLO weight file not found: {w_path}")
    if c_path.exists():
        model_handle = cv2.dnn.readNetFromDarknet(str(c_path), str(w_path))
        log.info("OpenCV Darknet backend loaded.")
    else:
        model_handle = cv2.dnn.readNetFromONNX(str(w_path))
        log.info("OpenCV ONNX backend loaded.")
    class_name_map = {i: f"class_{i}" for i in range(1000)}


def norm(arr: np.ndarray) -> np.ndarray:
    arr = np.asarray(arr, np.float32)
    return arr.reshape(-1, arr.shape[-1]).copy() if arr.ndim >= 2 else np.empty((0, 85), np.float32)


def flat(out) -> List[np.ndarray]:
    stk, res = [out], []
    while stk:
        itm = stk.pop()
        if isinstance(itm, np.ndarray):
            res.append(itm)
        elif isinstance(itm, (list, tuple)):
            stk.extend(itm)
    return res


def run_yolo_inference(frame_bgr, conf_thresh=0.25, iou_thresh=0.45, model_side=416, every_n_frames=1):
    """
    Run YOLO detection on the image and return bounding boxes.
    """
    global FRAME_COUNTER
    FRAME_COUNTER += 1
    if FRAME_COUNTER % every_n_frames:
        return []

    load_model_once()
    h, w = frame_bgr.shape[:2]
    inp = cv2.resize(frame_bgr, (model_side, model_side))
    blob = cv2.dnn.blobFromImage(inp, 1 / 255.0, (model_side, model_side), swapRB=True, crop=False)
    model_handle.setInput(blob)
    try:
        raw_out = model_handle.forward(model_handle.getUnconnectedOutLayersNames())
    except Exception:
        raw_out = model_handle.forward()

    boxes, confs, cls_ids = [], [], []
    for arr in flat(raw_out):
        for det in norm(arr):
            scores = det[5:]
            cls_id = int(np.argmax(scores))
            conf = float(scores[cls_id])
            if conf < conf_thresh:
                continue
            cx, cy, bw, bh = det[0:4] * model_side
            x1, y1 = int((cx - bw / 2) * w / model_side), int((cy - bh / 2) * h / model_side)
            x2, y2 = int((cx + bw / 2) * w / model_side), int((cy + bh / 2) * h / model_side)
            boxes.append([max(0, x1), max(0, y1), min(w - 1, x2), min(h - 1, y2)])
            confs.append(conf)
            cls_ids.append(cls_id)

    idxs = cv2.dnn.NMSBoxes(boxes, confs, conf_thresh, iou_thresh)
    idxs = idxs.flatten() if hasattr(idxs, "flatten") else idxs

    detections: List[Dict[str, object]] = []
    for i in idxs:
        x1, y1, x2, y2 = boxes[int(i)]
        detections.append(
            dict(
                label=class_name_map.get(cls_ids[int(i)], str(cls_ids[int(i)])),
                confidence=confs[int(i)],
                left=x1,
                top=y1,
                right=x2,
                bottom=y2,
            )
        )
    return detections


def display_yolo_on_camera_feed(frame_bgr: np.ndarray, detections: List[Dict[str, object]]) -> np.ndarray:
    """
    Draw YOLO detection boxes and labels on the frame.
    """
    for d in detections:
        l, t, r, b = d["left"], d["top"], d["right"], d["bottom"]
        cv2.rectangle(frame_bgr, (l, t), (r, b), (0, 255, 0), 2)
        cv2.putText(
            frame_bgr,
            f"{d['label']} {d['confidence']:.2f}",
            (l, max(0, t - 6)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )
    return frame_bgr


if __name__ == "__main__":  # pragma: no cover
    import sys

    if len(sys.argv) < 2:
        sys.exit(1)
    img = cv2.imread(sys.argv[1])
    if img is None:
        sys.exit(1)
    dets = run_yolo_inference(img)
    display_yolo_on_camera_feed(img, dets)
    cv2.imshow("YOLO result", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()