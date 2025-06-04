"""
shape_tracker.py  –  full drop‑in replacement
-------------------------------------------------
2D/3D Kalman‑based multi‑object tracker with stricter life‑cycle rules.
Changes vs. original:
• stable_age filter is enforced when tracks are returned
• stable_age reset whenever a frame is missed (track.lost++)
• adaptive matching radius no longer grows without bound (lost bonus capped)
• max_lost clamped to a sane 1‒60 range
Everything else untouched.
"""

import threading
from typing import List, Dict, Any, Tuple, Optional, cast
from dataclasses import dataclass, field
import numpy as np
import cv2
from scipy.optimize import linear_sum_assignment

__all__ = ["ShapeTracker", "ShapeTrack"]

# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ShapeTrack:
    data: Dict[str, Any]
    age: int = 1
    stable_age: int = 0       # consecutive frames with valid depth mask, etc.
    lost: int = 0             # consecutive frames unseen
    id: int = -1
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    kf: Optional[cv2.KalmanFilter] = field(default=None, repr=False)


# ──────────────────────────────────────────────────────────────────────────────
# Utils
# ──────────────────────────────────────────────────────────────────────────────

class RobustTimeoutError(Exception):
    """Raised when an external call exceeds permitted duration."""


def robust_call(fn, *args, timeout: float = 2.0, retries: int = 2, **kwargs):
    """Run *fn* with retries + timeout, return its result or raise."""
    exc: Optional[Exception] = None

    def wrap(holder):
        try:
            holder.append(fn(*args, **kwargs))
        except Exception as e:
            holder.append(e)

    for _ in range(retries):
        holder: List[Any] = []
        t = threading.Thread(target=wrap, args=(holder,))
        t.daemon = True
        t.start()
        t.join(timeout)
        if not holder:
            continue  # timed out
        if isinstance(holder[0], Exception):
            exc = holder[0]
            continue
        return holder[0]

    raise RobustTimeoutError(
        f"Timeout/failure on call {fn.__name__} after {retries} retries: {exc}"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Tracker
# ──────────────────────────────────────────────────────────────────────────────

class ShapeTracker:
    id_counter: int = 0

    # constants governing stricter behaviour ----------------------------------
    _LOST_BONUS_CAP = 5   # frames – limits how far the radius can inflate
    _MAX_LOST_CLAMP = 60  # frames – global upper bound for slider

    # -------------------------------------------------------------------------
    def __init__(self) -> None:
        self.tracks: Dict[str, List[ShapeTrack]] = {}
        self.candidates: Dict[str, List[Dict[str, Any]]] = {}

    # -------------------------------------------------------------------------
    @classmethod
    def next_id(cls) -> int:
        cls.id_counter += 1
        return cls.id_counter

    # -------------------------------------------------------------------------
    @staticmethod
    def validate_detection(det: Dict[str, Any]) -> None:
        if not isinstance(det, dict):
            raise ValueError("Each detection must be a dict.")
        if not set(det).intersection({"x", "y", "z", "cx", "cy"}):
            raise ValueError(f"Detection missing position: {det}")

    # -------------------------------------------------------------------------
    @staticmethod
    def pos_get(det: Dict[str, Any]) -> Tuple[float, float, float]:
        x = det.get("x", det.get("cx", 0.0))
        y = det.get("y", det.get("cy", 0.0))
        z = det.get("z", 0.0)
        return float(x), float(y), float(z)

    # -------------------------------------------------------------------------
    @staticmethod
    def track_distance(tr: ShapeTrack, det: Dict[str, Any]) -> float:
        tx, ty, tz = ShapeTracker.pos_get(tr.data)
        dx, dy, dz = ShapeTracker.pos_get(det)
        return float(np.sqrt((tx - dx) ** 2 + (ty - dy) ** 2 + (tz - dz) ** 2))

    # -------------------------------------------------------------------------
    @staticmethod
    def init_kf(det: Dict[str, Any], q2d: float, r2d: float, q3d: float, r3d: float) -> cv2.KalmanFilter:
        """Create a Kalman filter matching the dimensionality of *det*."""
        if all(k in det for k in ("x", "y", "z")):
            kf = cv2.KalmanFilter(6, 3, 0, cv2.CV_32F)
            dt = 1.0
            kf.transitionMatrix = np.array([
                [1, 0, 0, dt, 0, 0],
                [0, 1, 0, 0, dt, 0],
                [0, 0, 1, 0, 0, dt],
                [0, 0, 0, 1, 0, 0],
                [0, 0, 0, 0, 1, 0],
                [0, 0, 0, 0, 0, 1],
            ], np.float32)
            kf.measurementMatrix = np.eye(3, 6, dtype=np.float32)
            kf.processNoiseCov = np.eye(6, dtype=np.float32) * q3d
            kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * r3d
            kf.errorCovPost = np.eye(6, dtype=np.float32)
            kf.statePost[:3, 0] = np.array([det["x"], det["y"], det["z"]], dtype=np.float32)
        else:
            kf = cv2.KalmanFilter(4, 2, 0, cv2.CV_32F)
            dt = 1.0
            kf.transitionMatrix = np.array([
                [1, 0, dt, 0],
                [0, 1, 0, dt],
                [0, 0, 1, 0],
                [0, 0, 0, 1],
            ], dtype=np.float32)
            kf.measurementMatrix = np.eye(2, 4, dtype=np.float32)
            kf.processNoiseCov = np.eye(4, dtype=np.float32) * q2d
            kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * r2d
            kf.errorCovPost = np.eye(4, dtype=np.float32)
            kf.statePost[:2, 0] = np.array([
                det.get("cx", det.get("x", 0)),
                det.get("cy", det.get("y", 0)),
            ], dtype=np.float32)
        return kf

    # -------------------------------------------------------------------------
    def clear(self) -> None:
        self.tracks.clear()
        self.candidates.clear()
        ShapeTracker.id_counter = 0

    # ────────────────────────────────────────────────────────────────────────
    # MAIN TRACKING METHOD
    # ────────────────────────────────────────────────────────────────────────

    def track(
        self,
        shape: str,
        color: str,
        detections: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Update tracks for (shape, color) and return current visible tracks."""
        key = f"{shape}_{color}"

        # 1. Validation --------------------------------------------------------
        for det in detections:
            self.validate_detection(det)

        # 2. Extract runtime parameters ---------------------------------------
        alpha = float(params.get("tr_alpha", 5)) / 100.0
        base_valid = float(params.get("match_dist", 1500))
        max_lost = int(params.get("max_lost", 30))
        spawn_need = int(params.get("spawn_persist", 3))
        speed_gain = float(params.get("speed_gain", 0)) / 10.0
        lost_gain = float(params.get("LostGain", 5))
        q2d = float(params.get("kf_q_2d", 2)) / 1000.0
        r2d = float(params.get("kf_r_2d", 5)) / 1000.0
        q3d = float(params.get("kf_q_3d", 10)) / 1000.0
        r3d = float(params.get("kf_r_3d", 9)) / 1000.0
        min_stable_age = int(params.get("stable_age", 3))

        if alpha < 0 or not (0 < base_valid < 50000):
            raise ValueError("Unreasonable parameters for alpha or match_dist.")

        # clamp unrealistically large lost window
        max_lost = max(1, min(max_lost, self._MAX_LOST_CLAMP))

        # 3. Prep Kalman noise matrices ---------------------------------------
        tracks: List[ShapeTrack] = self.tracks.get(key, [])
        for tr in tracks:
            if tr.kf is None:
                continue
            if tr.kf.statePre.shape[0] == 6:
                tr.kf.processNoiseCov = np.eye(6, dtype=np.float32) * q3d
                tr.kf.measurementNoiseCov = np.eye(3, dtype=np.float32) * r3d
            else:
                tr.kf.processNoiseCov = np.eye(4, dtype=np.float32) * q2d
                tr.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * r2d

            pred = robust_call(tr.kf.predict, timeout=1.5)
            if pred.shape[0] == 6:
                tr.data.update({"x": float(pred[0]), "y": float(pred[1]), "z": float(pred[2])})
                tr.vx, tr.vy, tr.vz = map(float, pred[3:6, 0])
            else:
                tr.data.update({"cx": float(pred[0]), "cy": float(pred[1])})
                tr.vx, tr.vy = float(pred[2]), float(pred[3])
                tr.vz = 0.0

        # 4. Hungarian matching -----------------------------------------------
        matched_t, matched_d = set(), set()
        if tracks and detections and linear_sum_assignment is not None:
            m, n = len(tracks), len(detections)
            BIG = 1e6
            cost = np.full((m, n), BIG, dtype=np.float32)
            for ti, tr in enumerate(tracks):
                adapt_th = (
                    base_valid
                    + speed_gain * np.linalg.norm([tr.vx, tr.vy, tr.vz])
                    + lost_gain * min(tr.lost, self._LOST_BONUS_CAP)  # capped
                )
                for di, det in enumerate(detections):
                    d = self.track_distance(tr, det)
                    if d <= adapt_th:
                        cost[ti, di] = d
            ti_inds, di_inds = robust_call(linear_sum_assignment, cost, timeout=2.0)
            for ti, di in zip(ti_inds, di_inds):
                if cost[ti, di] >= BIG:
                    continue
                tr = tracks[ti]
                det = detections[di]

                # Kalman correction ----------------------------------------
                meas = []
                for k in ("x", "y", "z"):
                    if k in det:
                        meas.append(det[k])
                    elif k == "x" and "cx" in det:
                        meas.append(det["cx"])
                    elif k == "y" and "cy" in det:
                        meas.append(det["cy"])
                meas = np.array(meas, dtype=np.float32).reshape(-1, 1)
                if tr.kf is not None and meas.size == tr.kf.measurementMatrix.shape[0]:
                    _ = robust_call(tr.kf.correct, meas, timeout=1.5)

                # Copy/update data -----------------------------------------
                for k, v in det.items():
                    if k in ("x", "y", "z", "cx", "cy"):
                        tr.data[k] = v
                    elif isinstance(v, (int, float)):
                        tr.data[k] = float(tr.data.get(k, 0)) * (1 - alpha) + v * alpha
                    else:
                        tr.data[k] = v

                tr.age += 1
                if det.get("depth_mask_valid", False):
                    tr.stable_age += 1
                else:
                    tr.stable_age = 0  # failed validity resets consecutive counter
                tr.lost = 0
                matched_t.add(ti)
                matched_d.add(di)

        # 5. Update lost counters / reset maturity -----------------------------
        for ti, tr in enumerate(tracks):
            if ti not in matched_t:
                tr.lost += 1
                tr.stable_age = 0  # maturity evaporates when object not seen

        # 6. Spawn tracks from candidates --------------------------------------
        cands = self.candidates.get(key, [])
        new_cands: List[Dict[str, Any]] = []
        for di, det in enumerate(detections):
            if di in matched_d or det.get("r", 0) < 25:
                continue
            close = False
            for cand in cands:
                if self.track_distance(cand["det"], det) <= base_valid:
                    cand["det"] = det
                    cand["seen"] += 1
                    close = True
                    break
            if not close:
                new_cands.append({"det": det, "seen": 1})

        updated_cands = []
        for cand in cands + new_cands:
            if cand["seen"] >= spawn_need:
                tracks.append(
                    ShapeTrack(
                        data=dict(cand["det"]),
                        id=self.next_id(),
                        kf=self.init_kf(cand["det"], q2d, r2d, q3d, r3d),
                    )
                )
            else:
                updated_cands.append(cand)

        # 7. Prune old tracks --------------------------------------------------
        self.candidates[key] = updated_cands
        self.tracks[key] = [tr for tr in tracks if tr.lost <= max_lost]

        # 8. Build output list (visible + mature) ------------------------------
        results: List[Dict[str, Any]] = []
        for tr in self.tracks[key]:
            if tr.lost == 0 and tr.stable_age >= min_stable_age:
                results.append({
                    **tr.data,
                    "track_id": tr.id,
                    "age": tr.age,
                    "stable_age": tr.stable_age,
                })
        return results
