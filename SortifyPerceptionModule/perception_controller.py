"""
perception_controller.py
Controls the whole perception system. Takes camera frames, processes them,
finds objects, checks with AI if needed, keeps track of objects, and sends the results to the robot.
Author: Azi Sami (2025)
"""
from typing import List, Dict, Tuple
import time, math, cv2, numpy as np
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import socket
UDP_IP = "127.0.0.1"     # localhost
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

UDP_IP2 = "127.0.0.1"
UDP_PORT2 = 5006
sock2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock2.bind((UDP_IP2, UDP_PORT2))

BUFFER_SIZE = 65535


from debug_visualization import draw_scoring_overlay
from position_estimation import transform_camera_to_robot, estimate_position
#from hardware import DepthAICamera
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
    USE_GUI, USE_TRACKBARS, ENABLE_YOLO
)

DetectionData = Dict[str, float]
DetectionObj = Dict[str, object]
TrackedOutput = Dict[str, object]


class PerceptionController:
    """
    Runs the vision pipeline and sends data to the robot.
    """

    def __init__(self, node_name: str = "perception_controller") -> None:
        self.ros = ROSInterface(node_name)
        #self.camera = DepthAICamera(CAMERA_WIDTH, CAMERA_HEIGHT, CAMERA_FPS)
        #self.video = cv2.VideoCapture("test_video")
        #self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
        #self.video = cv2.VideoCapture("test_vest2.mp4")
        #if not self.video.isOpened():
        #    raise FileNotFoundError("test_video.mp4 not found or failed to open.")



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
            cv2.resizeWindow(TRACKBAR_WINDOW, 300, 300)
            create_trackbars(SLIDER_CONFIG, groups=ACTIVE_GROUPS)
        for tr in self.trackers.values():
            tr.clear()
        ShapeTracker.id_counter = 0
        #self.camera.start()
        #self._fx, self._fy, self._cx0, self._cy0 = self.camera.get_intrinsics()

    def get_video_frame(self):
        ret, frame = self.video.read()
        if not ret:
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.video.read()
        return frame if ret else None





    def process_frames(self) -> None:
        fps_timer = time.time()
        fps_count = 0
        fps_avg = 0.0
        while True:
            # 1. Get frames
            data, addr = sock2.recvfrom(BUFFER_SIZE)
            np_arr = np.frombuffer(data, dtype=np.uint8)
            color_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            if color_frame is None:
                print("End of video or failed to read frame.")
                break  # or return, depending on how you want to exit

            depth_frame = np.zeros_like(color_frame[:, :, 0])  # dummy depth


            #in_video, in_depth = self.camera.get_latest_frames()
            self.global_frame_counter += 1
            params = get_runtime_params()
            #color_frame, depth_frame = in_video.getCvFrame(), in_depth.getFrame()
            #if color_frame is None or depth_frame is None:
            #    raise RuntimeError("Camera returned None frame.")
            #color_frame, depth_frame = map(lambda f: cv2.flip(f, -1), (color_frame, depth_frame))
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

            # 4. AI check (optional) – full frame only for overlay
            ai_confirmed = False
            overlay_with_yolo = base_image.copy()
            if ENABLE_YOLO:
                detections_ai = run_yolo_inference(base_image)
                ai_confirmed = bool(detections_ai)
                for det in detections_ai:
                    l, t, r, b = det["left"], det["top"], det["right"], det["bottom"]
                    cv2.rectangle(overlay_with_yolo, (l, t), (r, b), (0, 255, 0), 2)
                    cv2.putText(
                        overlay_with_yolo, f'{det["label"]} {det["confidence"]:.2f}',
                        (l, t - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2
                    )

            # 5. Position/filter
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


            # 6. Run YOLO per detection_post
            for obj in detections_post:
                d = obj["data"]
                if ENABLE_YOLO:
                    cx, cy, r = map(int, map(round, (d["cx"], d["cy"], d.get("r", 40))))
                    r_pad = max(20, int(r * 1.4))
                    x1 = max(0, cx - r_pad)
                    y1 = max(0, cy - r_pad)
                    x2 = min(base_image.shape[1], cx + r_pad)
                    y2 = min(base_image.shape[0], cy + r_pad)
                    crop = base_image[y1:y2, x1:x2]
                    d["ai_valid"] = bool(run_yolo_inference(crop))
                else:
                    d["ai_valid"] = False
                d["tracker_valid"] = False
            
            """
            # 7. Track everything  (complete, working block)
            dets_by_type: Dict[Tuple[str, str], List[DetectionData]] = {}
            for obj in detections_post:                         # ← keep these two lines
                dets_by_type.setdefault((obj["shape"], obj["color"]), []).append(obj["data"])

            all_tracked: List[TrackedOutput] = []
            for (shape, color), det_list in dets_by_type.items():
                tracker = self.trackers.setdefault((shape, color), ShapeTracker())
                for t in tracker.track(shape, color, det_list, params):
                    t["tracker_valid"] = True                   # every returned track is mature
                    all_tracked.append({"shape": shape, "color": color, "data": t})


            # 8. Scoring
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
                    """
            
            # 7–8. Stateless passthrough
            tracked: List[TrackedOutput] = []
            for obj in detections_post:
                d = obj["data"]
                d["accepted"] = True
                d["score"] = 999  # optional dummy value
                d["tracker_valid"] = False
                tracked.append(obj)



            # 9. Publish
            for det in tracked:
                d = det["data"]
                if not all(k in d for k in ("x_mm", "y_mm", "z_mm")):
                    continue
                xr, yr, zr = transform_camera_to_robot(d["x_mm"], d["y_mm"], d["z_mm"])
                self.ros.publish(det["shape"], det["color"], d.get("track_id", 255), xr, yr, zr)

            # Vest detected?
            vest_detected = any(
                det["shape"] == "rectangle" and det["color"] == "neon_yellow"
                for det in tracked
            )

            # Send to UDP_IP and Port if detected
            msg = b"1" if vest_detected else b"0"
            sock.sendto(msg, (UDP_IP, UDP_PORT))

            
            # 10. Visualization
            #np_arr = np.frombuffer(data, dtype=np.uint8)
            #overlay = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            #img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            overlay = base_image.copy()
            #draw_detections(img, tracked)
            #draw_scoring_overlay(img,tracked)
            draw_detections(overlay, tracked)
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
                DetectColor.neon_yellow(hsv, params),
                #img,
                overlay
            )
            debug_img = cv2.resize(debug_img, (0, 0), fx=0.5, fy=0.5)



            # 11. Logging
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


            #if self.video.isOpened():
                #_, preview = self.video.read()
                #if preview is not None:
                    #cv2.imshow("Video Preview", preview)


            # 12. Show/debug/log
            if USE_GUI:
                foc = int(params.get("focus", 0))
                #if foc != self._prev_focus:
                    #self.camera.set_focus(foc)
                    #self._prev_focus = foc
                #cv2.imshow("Test Image", self.image)
                cv2.imshow("Debug View", debug_img)



                #cv2.resizeWindow("Debug View", 640, 360)


                #cv2.imshow("Unity View", img)



                if self.handle_key_press(cv2.waitKey(1) & 0xFF, base_image):
                    break

        cv2.destroyAllWindows()
        #self.camera.shutdown()
        self.video.release()
        self.ros.destroy()
        ros_shutdown()


    def handle_key_press(self, key: int, frame: np.ndarray) -> bool:
        # Button presses
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

