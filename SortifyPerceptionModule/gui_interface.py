"""
gui_interface.py

Handles creation of OpenCV trackbars and reading live parameter values.
Allows the whole pipeline to run headless if GUI is off.
"""

from __future__ import annotations

from typing import Any, Dict, List

import cv2

from config import (
    SLIDER_CONFIG,
    TRACKBAR_WINDOW,
    ACTIVE_GROUPS,
    USE_GUI,
    USE_TRACKBARS,
)

__all__ = ["create_trackbars", "get_runtime_params"]

GROUPS_FALLBACK = ACTIVE_GROUPS


def noop(_: int) -> None:
    # Placeholder for OpenCV trackbar callback
    ...


def create_trackbars(
    cfg: Dict[str, Dict[str, Any]] | None = None,
    groups: List[str] | None = None,
) -> None:
    """
    Create OpenCV trackbars for the selected parameter groups.
    Does nothing if GUI/trackbars are disabled.
    """    

    if not (USE_GUI and USE_TRACKBARS):
        return 

    cfg = cfg or SLIDER_CONFIG
    groups = groups or GROUPS_FALLBACK

    cv2.namedWindow(TRACKBAR_WINDOW, cv2.WINDOW_NORMAL)

    for name, settings in cfg.items():
        if settings.get("group") not in groups:
            continue
        cv2.createTrackbar(
            name,
            TRACKBAR_WINDOW,
            int(settings.get("default", 0)),
            int(settings.get("max", 100)),
            noop,
        )

def get_runtime_params(groups: List[str] | None = None) -> Dict[str, Any]:
    """
    Get current parameter values from all active trackbars.
    If GUI is off or sliders are missing, falls back to default values in SLIDER_CONFIG.
    """
    groups = groups or GROUPS_FALLBACK

    hard_defaults = {
        "R1 H min": 0, "R1 H max": 6, "R2 H min": 170, "R2 H max": 180,
        "R S min": 100, "R S max": 255, "R V min": 70, "R V max": 255,
        "B H min": 95, "B H max": 145, "B S min": 100, "B S max": 255,
        "B V min": 65, "B V max": 255,
        "G H min": 40, "G H max": 100, "G S min": 105, "G S max": 255,
        "G V min": 35, "G V max": 255,
        "Y H min": 20, "Y H max": 35, "Y S min": 100, "Y S max": 255,
        "Y V min": 100, "Y V max": 255,
        "kernel_size": 0, "open_iter": 0, "close_iter": 0,
        "dp": 20, "minDist": 40, "param1": 200, "param2": 60,
        "minRadius": 25, "maxRadius": 90, "c_area": 2500,
        "c_mask_thr": 65, "c_circ": 80, "c_iou_thr": 60,
        "s_sol": 7, "s_ext": 85, "s_min_area": 5000, "s_max_area": 80000,
        "s_eps": 50, "s_asp_min": 60, "s_asp_max": 110, "s_circ": 88, "s_iou_thr": 60,
        "Color Weight": 33, "Shape Weight": 33, "AI Weight": 100,
        "Depth Weight": 66, "Depth Mask Weight": 100,
        "Tracker Weight": 100, "Decision Accept Threshold": 300,
        "focus": 130, "tr_alpha": 5, "match_dist": 1500, "max_lost": 30,
        "spawn_persist": 0, "speed_gain": 0, "stable_age": 2,
        "kf_q_2d": 2, "kf_r_2d": 5, "kf_q_3d": 10, "kf_r_3d": 9,
        "clahe_clip": 0, "gaussian_k": 5, "gaussian_sigma": 0, "gray": 1
    }

    if not (USE_GUI and USE_TRACKBARS):
        return {
            name: cfg.get("default", hard_defaults.get(name, 0))
            for name, cfg in SLIDER_CONFIG.items()
        } | {
            k: v for k, v in hard_defaults.items() if k not in SLIDER_CONFIG
        }

    params: Dict[str, Any] = {}
    for name, cfg in SLIDER_CONFIG.items():
        if groups and cfg.get("group") not in groups and name not in hard_defaults:
            continue
        try:
            params[name] = cv2.getTrackbarPos(name, TRACKBAR_WINDOW)
        except cv2.error:
            params[name] = cfg.get("default", hard_defaults.get(name, 0))

    return params

