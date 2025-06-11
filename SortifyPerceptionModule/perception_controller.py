"""
perception_controller.py
Controls the whole perception system. Takes camera frames, processes them,
finds objects, checks with AI if needed, keeps track of objects, and sends the results to the robot.
Author: Azi Sami (2025)
"""
from typing import List, Dict, Tuple
import time, math, cv2, numpy as np

from debug_visualization import draw_scoring_overlay
from position_estimation import transform_camera_to_robot, estimate_position
from preprocessing import preprocess                        
from detection import detect_objects, DetectColor
from scoring_controller import DecisionResult, merge_detection_info
from shape_tracker import ShapeTracker
from debug_visualization import draw_detections, build_debug_view
from gui_interface import create_trackbars, get_runtime_params
from logging_handler import logger as console_logger, KPIBatchLogger
from ros_wrapper import ROSInterface, ros_shutdown
from yolo_verification import run_yolo_inference         
from config import (
    CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS,
    SLIDER_CONFIG, TRACKBAR_WINDOW, TRACK_TARGETS, ACTIVE_GROUPS,
    LOGGING_TOGGLE_KEY, LOGGING_MAX_FRAMES_DEFAULT,
    DEPTH_MIN_MM, DEPTH_MAX_MM, GROUND_TRUTH_POS,
    USE_GUI, USE_TRACKBARS, ENABLE_YOLO, MODE, DRAW_DETECTIONS, DRAW_SCORING, DEBUG_LAYOUT
)

DetectionData = Dict[str, float]
DetectionObj = Dict[str, object]
TrackedOutput = Dict[str, object]


class PerceptionController:
    """
    Runs the vision pipeline based on selected mode.
    """
    def __init__(self, node_name: str = "perception_controller") -> None:
        if MODE == "sortify":
            from hardware import DepthAICamera
            self.camera = DepthAICamera(CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS)
            self.ros = ROSInterface(node_name)
        elif MODE == "demo":
            self.video = cv2.VideoCapture(1)  # Webcam
        elif MODE == "safety":
            import socket
            self.udp_ip = "127.0.0.1"
            self.udp_port2 = 5006
            self.udp_sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.udp_sock2.bind((self.udp_ip, self.udp_port2))

        self.yolo_verified_buffer = [] 
        self._fx = self._fy = self._cx0 = self._cy0 = 0.0
        self._prev_focus = -1
        self.trackers: Dict[Tuple[str, str], ShapeTracker] = {
            (t["shape"], t["color"]): ShapeTracker() for t in TRACK_TARGETS
        }
        self.global_frame_counter = 0
        self.kpi_logger = None
        self.logging_start_frame = None

    def initialize(self) -> None:
        """
        Sets up the GUI, trackers, camera, and calibration.
        """
        if USE_GUI and USE_TRACKBARS:
            cv2.namedWindow(TRACKBAR_WINDOW, cv2.WINDOW_NORMAL)
            create_trackbars(SLIDER_CONFIG, groups=ACTIVE_GROUPS)
        for tr in self.trackers.values():
            tr.clear()
        ShapeTracker.id_counter = 0
        if MODE == "sortify":
            self.camera.start()
            self._fx, self._fy, self._cx0, self._cy0 = self.camera.get_intrinsics()
    
    def send_output(self, shape, color, data, accepted):
        if MODE == "sortify":
            if self.ros and all(k in data for k in ("x_mm", "y_mm", "z_mm")):
                xr, yr, zr = transform_camera_to_robot(data["x_mm"], data["y_mm"], data["z_mm"])
                self.ros.publish(shape, color, data.get("track_id", 255), xr, yr, zr)
        elif MODE == "safety":
            import socket
            vest_detected = shape == "rectangle" and color == "neon_yellow" and accepted
            msg = b"1" if vest_detected else b"0"
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(msg, ("127.0.0.1", 5005))
            sock.close()
        # MODE == "demo" → no output

    def get_video_frame(self):
        if MODE == "sortify":
            return self.camera.get_latest_frames()
        elif MODE == "demo":
            ret, frame = self.video.read()
            if not ret:
                return None, None
            depth_dummy = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
            return frame, depth_dummy
        elif MODE == "safety":
            data, _ = self.udp_sock2.recvfrom(65535)
            np_arr = np.frombuffer(data, dtype=np.uint8)
            frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            depth_dummy = np.zeros_like(frame[:, :, 0])
            return frame, depth_dummy
        
    def compute_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        iou = interArea / float(boxAArea + boxBArea - interArea + 1e-6)
        return iou




    def process_frames(self) -> None:
        fps_timer = time.time()
        fps_count = 0
        fps_avg = 0.0

        while True:
            # 1. Get frames
            color_frame, depth_frame = self.get_video_frame()
            if color_frame is None or depth_frame is None:
                raise RuntimeError("Camera returned None frame.")


            if self.global_frame_counter % 3 == 0:
                self.cached_params = get_runtime_params()
            params = self.cached_params

            if color_frame is None or depth_frame is None:
                raise RuntimeError("Camera returned None frame.")
            base_image = color_frame.copy()

            # 2. Preprocess
            processed = preprocess(
                frame_bgr=color_frame,
                use_clahe=params["clahe_clip"] > 0,
                clahe_clip=float(params["clahe_clip"]),
                blur_k=int(params["gaussian_k"]),
                use_gray=False,
            )

            # 3. Detect objects (classic CV)
            detections_raw: List[DetectionObj] = detect_objects(processed, params)
            detections_post: List[DetectionObj] = []


            # 4. Position/filter
            for obj in detections_raw:
                data2d = obj["data"]
                pos3d = estimate_position(
                    data2d, depth_frame,
                    fx=self._fx, fy=self._fy, cx0=self._cx0, cy0=self._cy0,
                    mask=obj.get("mask") or data2d.get("mask"),
                )
                data2d["depth_mask_valid"] = pos3d["depth_mask_valid"]
                merged = merge_detection_info(obj, data2d, pos3d)
                obj["data"] = merged
                detections_post.append(obj)

            # AI model (optional)
            overlay_with_yolo = base_image.copy()
            detections_ai = run_yolo_inference(base_image) if ENABLE_YOLO else []

            verified_this_frame: list[dict] = []
            matched_ai = [False] * len(detections_ai)          

            for obj in detections_post:
                if not (ENABLE_YOLO and obj.get("shape")):
                    obj["data"]["ai_valid"] = False
                    continue

                d = obj["data"]
                cx, cy, r = int(d["cx"]), int(d["cy"]), int(d.get("r", 40))
                shape_box = (
                    max(0, cx - r), max(0, cy - r),
                    min(base_image.shape[1], cx + r), min(base_image.shape[0], cy + r)
                )

                best_iou, best_idx = 0.0, -1
                for idx, det in enumerate(detections_ai):
                    yolo_box = (det["left"], det["top"], det["right"], det["bottom"])
                    iou = self.compute_iou(shape_box, yolo_box)
                    if iou > best_iou:
                        best_iou, best_idx = iou, idx

                if best_iou > 0.15:
                    matched_ai[best_idx] = True       
                    d["ai_valid"] = True
                else:
                    d["ai_valid"] = False

            for idx, det in enumerate(detections_ai):
                if not matched_ai[idx]:
                    continue                         
                verified_this_frame.append({
                    "box": (det["left"], det["top"], det["right"], det["bottom"]),
                    "label": det["label"],
                    "conf": det["confidence"],
                    "ttl": 2,
                    "shape_id": idx,                
                })

            next_buf = []
            for e in self.yolo_verified_buffer:
                e["ttl"] -= 1
                if e["ttl"] > 0:
                    next_buf.append(e)
            self.yolo_verified_buffer = next_buf

            for v in verified_this_frame:
                hit = next((e for e in self.yolo_verified_buffer
                            if self.compute_iou(e["box"], v["box"]) > 0.2), None)
                if hit:
                    hit.update(box=v["box"], label=v["label"], conf=v["conf"], ttl=2)
                else:
                    self.yolo_verified_buffer.append(v)

            for e in self.yolo_verified_buffer:
                l, t, r, b = e["box"]
                cv2.rectangle(overlay_with_yolo, (l, t), (r, b), (0, 255, 0), 2)
                cv2.putText(
                    overlay_with_yolo,
                    f'{e["label"]} {e["conf"]:.2f}',
                    (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
                )


            # 6. Track everything
            if MODE in ("sortify", "demo"):
                dets_by_type: Dict[Tuple[str, str], List[DetectionData]] = {}
                for obj in detections_post:
                    dets_by_type.setdefault((obj["shape"], obj["color"]), []).append(obj["data"])

                all_tracked: List[TrackedOutput] = []
                for (shape, color), det_list in dets_by_type.items():
                    tracker = self.trackers.setdefault((shape, color), ShapeTracker())
                    for t in tracker.track(shape, color, det_list, params):
                        t["tracker_valid"] = True
                        all_tracked.append({"shape": shape, "color": color, "data": t})

                # 7. Scoring
                tracked: List[TrackedOutput] = []
                for det in all_tracked:
                    d = det["data"]
                    decision = DecisionResult.get_decision(d)
                    d["score"] = getattr(decision, "score", None)
                    d["accepted"] = decision.accepted
                    if decision.accepted:
                        shape, color = det["shape"], det["color"]
                        if (shape, color) in GROUND_TRUTH_POS:
                            gx, gy, gz = GROUND_TRUTH_POS[(shape, color)]
                            d["pos_err_mm"] = math.dist((d["x_mm"], d["y_mm"], d["z_mm"]), (gx, gy, gz))
                        else:
                            d["pos_err_mm"] = None
                        tracked.append(det)

            # 6–7. Stateless passthrough
            elif MODE == "safety":
                tracked: List[TrackedOutput] = []
                for obj in detections_post:
                    d = obj["data"]
                    d["accepted"] = True
                    d["score"] = 999  # dummy
                    d["tracker_valid"] = False
                    tracked.append(obj)

            # 8. Publish
            if MODE == "sortify":
                for det in tracked:
                    d = det["data"]
                    if not all(k in d for k in ("x_mm", "y_mm", "z_mm")):
                        continue
                    self.send_output(det["shape"], det["color"], d, accepted=d["accepted"])

            # 9. Visualization
            overlay = base_image.copy()
            if DRAW_DETECTIONS:
                draw_detections(overlay, tracked)
            if DRAW_SCORING:
                draw_scoring_overlay(overlay, tracked)


            fps_count += 1
            if (now := time.time()) - fps_timer >= 1:
                fps_avg = fps_count / (now - fps_timer)
                fps_timer, fps_count = now, 0
            cv2.putText(overlay, f"{fps_avg:.1f} FPS", (10, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (100, 255, 200), 2)

            depth_norm = np.clip((depth_frame.astype(np.float32) - DEPTH_MIN_MM)
                                * 255.0 / (DEPTH_MAX_MM - DEPTH_MIN_MM), 0, 255).astype(np.uint8)
            depth_vis = cv2.applyColorMap(depth_norm, cv2.COLORMAP_JET)
            hsv = cv2.cvtColor(processed, cv2.COLOR_BGR2HSV)
            
            debug_img = build_debug_view(
                DetectColor.red(hsv, params),
                DetectColor.blue(hsv, params),
                overlay_with_yolo,
                overlay
            ) if DEBUG_LAYOUT == "2x2" else np.vstack([overlay_with_yolo, overlay])


            # 10. Logging
            if self.kpi_logger and self.logging_start_frame is not None:
                rel = self.global_frame_counter - self.logging_start_frame
                if rel < LOGGING_MAX_FRAMES_DEFAULT:
                    self.kpi_logger.update(frame_rel=rel, detections=[
                        {**det["data"], "shape": det["shape"], "color": det["color"]} for det in tracked
                    ], fps_avg=fps_avg, overlay=overlay)
                else:
                    self.kpi_logger.close()
                    self.kpi_logger = self.logging_start_frame = None
                    console_logger.info("Logging STOPPED")

            # 11. Show/debug/log
            if USE_GUI:
                if MODE == "sortify":
                    foc = int(params.get("focus", 0))
                    if foc != self._prev_focus:
                        self.camera.set_focus(foc)
                        self._prev_focus = foc
                        
                cv2.imshow("Debug View", debug_img)
                if self.handle_key_press(cv2.waitKey(1) & 0xFF, base_image):
                    break

        cv2.destroyAllWindows()
        if MODE == "sortify" and hasattr(self, "ros"):
            self.ros.destroy()
            ros_shutdown()
        elif MODE == "demo" and hasattr(self, "video"):
            self.video.release()
        elif MODE == "safety" and hasattr(self, "udp_sock2"):
            self.udp_sock2.close()


    # Button presses
    def handle_key_press(self, key: int, frame: np.ndarray) -> bool:
        if key in (ord("s"), ord("p"), ord("q")): return True
        elif key == ord("r"):
            for n, v in SLIDER_CONFIG.items():
                if v.get("group") in ACTIVE_GROUPS:
                    cv2.setTrackbarPos(n, TRACKBAR_WINDOW, v["default"])
            console_logger.info("Trackbars RESET")             
        elif key == LOGGING_TOGGLE_KEY:
            if self.kpi_logger is None:
                self.kpi_logger = KPIBatchLogger(max_frames=LOGGING_MAX_FRAMES_DEFAULT)
                self.logging_start_frame = self.global_frame_counter
                console_logger.info("Logging STARTED")
            else:
                self.kpi_logger.close(); self.kpi_logger = self.logging_start_frame = None
                console_logger.info("Logging STOPPED")
        elif key == ord("f"):
        # Toggle fullscreen/windowed for Expo View
            self.expo_fullscreen = not getattr(self, "expo_fullscreen", False)
            if self.expo_fullscreen:
                cv2.setWindowProperty("Expo View", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
                console_logger.info("Expo View: FULLSCREEN")
            else:
                cv2.setWindowProperty("Expo View", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL)
                console_logger.info("Expo View: WINDOWED")

        return False


def main() -> None:
    ctl = PerceptionController(); ctl.initialize(); ctl.process_frames()


if __name__ == "__main__":
    main()

