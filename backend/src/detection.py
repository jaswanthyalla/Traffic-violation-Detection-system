"""
Detection Module
Handles object detection using YOLO models
"""
from ultralytics import YOLO
import cv2
import numpy as np
from typing import List, Dict, Tuple

class ObjectDetector:
    """Class for object detection using YOLO"""
    
    def __init__(self, model_path: str = "yolov8n.pt"):
        """
        Initialize object detector
        
        Args:
            model_path: Path to YOLO model file
        """
        print(f"Loading YOLO model: {model_path}")
        self.model = YOLO(model_path)
        self.confidence_threshold = 0.45
        
    def detect(self, frame: np.ndarray) -> List[Dict]:
        """
        Run detection on frame
        
        Args:
            frame: Input frame
            
        Returns:
            List of detections with class names and confidence scores
        """
        results = self.model(frame, conf=self.confidence_threshold)
        detections = []
        
        if results[0].boxes:
            for box in results[0].boxes:
                detection = {
                    'class': int(box.cls[0]),
                    'class_name': results[0].names[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': box.xyxy[0].tolist(),
                    'center': self._get_center(box.xyxy[0])
                }
                detections.append(detection)
        
        return detections
    
    @staticmethod
    def _get_center(bbox: list) -> Tuple[float, float]:
        """Calculate center of bounding box"""
        x1, y1, x2, y2 = bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
    
    def annotate_frame(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """
        Annotate frame with detections
        
        Args:
            frame: Input frame
            detections: List of detections
            
        Returns:
            Annotated frame
        """
        annotated = frame.copy()
        
        for det in detections:
            x1, y1, x2, y2 = [int(v) for v in det['bbox']]
            confidence = det['confidence']
            class_name = det['class_name']
            
            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw label
            label = f"{class_name}: {confidence:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        return annotated
    
    def set_confidence_threshold(self, threshold: float):
        """Set confidence threshold for detections"""
        self.confidence_threshold = threshold
