"""
preprocessing.py

Handles image preprocessing before detection.
Includes CLAHE (contrast), blurring, gray, and mask cleaning.
"""

import cv2
import numpy as np
from config import SLIDER_CONFIG


def apply_clahe(frame_bgr, clip_limit=2.0, tile_grid_size=(8, 8)):
    """
    Apply CLAHE (adaptive contrast) to BGR image.
    """
    lab = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_eq = clahe.apply(l)
    lab_eq = cv2.merge((l_eq, a, b))
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)


def apply_gaussian_blur(frame, kernel_size=5):
    """
    Blur image with Gaussian filter.
    """
    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
    return cv2.GaussianBlur(frame, (k, k), 0)


def apply_gray(frame):
    """
    Convert image to gray.
    """
    if len(frame.shape) == 2:
        return frame
    elif frame.shape[2] == 3:
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError("Invalid image for gray")


def preprocess(frame_bgr, use_clahe=True, clahe_clip=2.0, blur_k=5, use_gray=False):
    """
    Full preprocessing: CLAHE, blur, and gray as needed.
    """
    out = frame_bgr.copy()
    if use_clahe:
        out = apply_clahe(out, clip_limit=clahe_clip)
    if blur_k > 0:
        out = apply_gaussian_blur(out, kernel_size=blur_k)
    if use_gray:
        out = apply_gray(out)
    return out


def clean_mask(mask: np.ndarray, params: dict) -> np.ndarray:
    """
    Clean up binary mask using open/close morphology.
    """
    open_iter = int(params.get("open_iter", 1))
    close_iter = int(params.get("close_iter", 1))
    kernel_size = int(params.get("kernel_size"))

    k = max(1, kernel_size)
    if k % 2 == 0:
        k += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=open_iter)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=close_iter)
    return cleaned
