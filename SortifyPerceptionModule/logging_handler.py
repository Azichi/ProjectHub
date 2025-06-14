"""
logging_handler.py - KPI-logger

Uses LOG_COLUMNS from config to log data.
"""

from __future__ import annotations
import csv, os, time, logging, cv2
from datetime import datetime
from typing import List, Dict, Any, Optional, TextIO
from config import (
    TRACK_TARGETS,
    LOG_COLUMNS,         
    LOGGING_OUTPUT_DIR,
    LOGGING_MAX_FRAMES_DEFAULT,
    POS_ERROR_THRESHOLD_MM,
)

# Logger setup
logger = logging.getLogger("kpi_logger")
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

def key(shape: str, color: str) -> str:
    return f"{shape}_{color}"

def snap(img, path):
    try:
        cv2.imwrite(path, img)
    except Exception as e:
        logger.warning(f"[snap] {e}")

class ObjectStats:
    """Handles object statistics and CSV logging."""
    def __init__(self, shape: str, color: str, writer: csv.writer,
                fh: TextIO, max_frames: int, run_dir: str):
        self.fh = fh
        self.shape, self.color = shape, color
        self.writer = writer
        self.max_frames = max_frames
        self.run_dir = run_dir
        self.frames = 0
        self.detected = 0
        self.first_error_saved = False

    def finished(self) -> bool:
        return self.frames >= self.max_frames

    def update(self, *, frame: int, test_type: str,
            detection: Optional[Dict[str, Any]],
            fps: float, t0: float, img):
        """Updates stats and writes to CSV"""        

        self.frames += 1
        now = time.time() - t0
        pos_err = "NA"

        row = {
            "test_type": test_type,
            "frame": frame,
            "time_sec": f"{now:.3f}",
            "pos_error_mm": "NA",
            "fps": f"{fps:.2f}",
        }

        if detection:
            pos_err = detection.get("pos_err_mm", "NA")
            row["pos_error_mm"] = f"{pos_err:.2f}" if isinstance(pos_err, float) else pos_err

            for key in ("track_id", "shape", "color", "x_mm", "y_mm", "z_mm", 
                        "depth_valid", "depth_mask_valid", "color_valid", "shape_valid"):
                row[key] = detection.get(key, "NA")

        self.writer.writerow([row.get(col, "NA") for col in LOG_COLUMNS])


        if img is None: return
        if frame == 0:
            snap(img, os.path.join(self.run_dir, f"{self.color}_{self.shape}first.png"))
        elif frame == self.max_frames - 1:
            snap(img, os.path.join(self.run_dir, f"{self.color}_{self.shape}last.png"))
        elif not self.first_error_saved and (detection is None or
             (isinstance(pos_err, float) and pos_err > POS_ERROR_THRESHOLD_MM)):
            snap(img, os.path.join(self.run_dir, f"{self.color}_{self.shape}error.png"))
            self.first_error_saved = True

class KPIBatchLogger:
    """Handles batch logging for all objects."""
    def __init__(self, test_type: str,
                 max_frames: int = LOGGING_MAX_FRAMES_DEFAULT):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = os.path.join(LOGGING_OUTPUT_DIR, f"{ts}_{test_type}")
        os.makedirs(self.run_dir, exist_ok=True)
        self.test_type = test_type
        self.t0 = time.time()
        self.objs: Dict[str, ObjectStats] = {}
        for t in TRACK_TARGETS:
            shape, color = t["shape"], t["color"]
            fpath = os.path.join(self.run_dir, f"{color}_{shape}.csv")
            fh: TextIO = open(fpath, "w", newline="")
            w = csv.writer(fh)
            w.writerow(LOG_COLUMNS)
            self.objs[key(shape, color)] = ObjectStats(shape, color, w, fh, max_frames, self.run_dir)
            logger.info(f"[csv] {fpath}")

    def update(self, frame_rel: int, detections: List[Dict[str, Any]],
               fps_avg: float, overlay):
        """Updates each object's stats."""
        det_map = {key(d["shape"], d["color"]): d for d in detections}
        for key, obj in self.objs.items():
            if obj.finished(): continue
            obj.update(frame=frame_rel,
                       test_type=self.test_type,
                       detection=det_map.get(key),
                       fps=fps_avg, t0=self.t0, img=overlay)

    def active(self) -> bool:
        """Checks if there are any active objects."""
        return any(not o.finished() for o in self.objs.values())

    def close(self):
        """Closes all CSV files."""
        for o in self.objs.values():
            o.fh.close()                        
        logger.info("CSV-files closed.")
