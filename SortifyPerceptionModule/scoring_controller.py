"""
scoring_controller.py

Handles per-object scoring and the accept/reject decision based on various parameters.
"""

from config import SLIDER_CONFIG
from gui_interface import get_runtime_params
from typing import Dict, Any


class DecisionResult:
    """
    Holds the result of the decision (accepted or rejected) and the reason for the decision.
    """    
    def __init__(self, accepted: bool, reason: str, label: str):
        self.accepted = accepted
        self.reason = reason
        self.label = label

    @staticmethod
    def weights(params: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Return the weights for each factor (color, shape, AI, etc.) based on the current parameters.
        """
        if params is None:
            params = get_runtime_params()

        return {
            k: params.get(k, SLIDER_CONFIG.get(k, {}).get("default", 0.0)) / 100 
            for k in (
                "Color Weight", "Shape Weight", "AI Weight",
                "Depth Weight", "Depth Mask Weight", "Tracker Weight",
                "Decision Accept Threshold"
            )
        }

    @staticmethod
    def get_decision(raw: Dict[str, Any]) -> "DecisionResult":
        """
        Calculate the score for an object and make a decision to accept or reject.
        """
        weights = DecisionResult.weights()

        # Construct the label for tracking
        label = f"{raw.get('color', 'unknown')}_{raw.get('shape', 'unknown')}"
        
        # Initialize score and calculate based on validation flags
        score = 0.0
        score += (1 if raw.get("color_valid", False) else 0) * weights["Color Weight"]
        score += (1 if raw.get("shape_valid", False) else 0) * weights["Shape Weight"]
        score += (1 if raw.get("ai_valid", False) else 0) * weights["AI Weight"]
        score += (1 if raw.get("depth_valid", False) else 0) * weights["Depth Weight"]
        score += (1 if raw.get("depth_mask_valid", False) else 0) * weights["Depth Mask Weight"]
        score += (1 if raw.get("tracker_valid", False) else 0) * weights["Tracker Weight"]

        # Check if score is above the threshold
        threshold = weights["Decision Accept Threshold"]

        # Debug output for score details
        #print("\n[ScoringController] Scores:")
        #print(f"  color_valid:        {raw.get('color_valid')}   -> weight: {weights['Color Weight']:.2f}")
        #print(f"  shape_valid:        {raw.get('shape_valid')}   -> weight: {weights['Shape Weight']:.2f}")
        #print(f"  ai_valid:           {raw.get('ai_valid')}      -> weight: {weights['AI Weight']:.2f}")
        #print(f"  depth_valid:        {raw.get('depth_valid')}   -> weight: {weights['Depth Weight']:.2f}")
        #print(f"  depth_mask_valid:   {raw.get('depth_mask_valid')}   -> weight: {weights['Depth Mask Weight']:.2f}")
        #print(f"  tracker_valid:      {raw.get('tracker_valid')} -> weight: {weights['Tracker Weight']:.2f}")

        #print(f"\n[ScoringController] Total Score: {score:.2f}")
        #print(f"[ScoringController] Threshold:   {threshold:.2f}")

        # Accept or reject based on the score
        if score >= threshold:
            return DecisionResult(True, "ok", label)
        else:
            result = DecisionResult(False, "low_score", label)
        result.score = score
        return result


def merge_detection_info(obj: Dict[str, Any], shape_data: Dict[str, Any], pos_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge detection, shape, and position data into one dictionary.
    """
    merged = dict(shape_data)
    
    # Merge position data with defaults if keys are missing
    merged.update({
        "x_mm": pos_data.get("x_mm", 0.0),
        "y_mm": pos_data.get("y_mm", 0.0),
        "z_mm": pos_data.get("z_mm", 0.0),
        "depth_valid": pos_data.get("depth_valid", False),
        "depth_mask_valid": pos_data.get("depth_mask_valid", False),
        "color_valid": obj.get("color") is not None,
        "shape_valid": obj.get("shape") is not None,
        "color": obj.get("color", "unknown"),
        "shape": obj.get("shape", "unknown"),
        "ai_valid": shape_data.get("ai_valid", False),
        "tracker_valid": shape_data.get("tracker_valid", False),
        "track_id": shape_data.get("track_id", "?"),
    })
    
    return merged
