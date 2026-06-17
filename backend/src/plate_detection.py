"""
License Plate Detection Module
Detects and extracts license plates from vehicles
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional

class PlateDetector:
    """Class for detecting license plates"""
    
    def __init__(self, plate_model_path: str = "models/yolo_plate.pt"):
        """
        Initialize plate detector
        
        Args:
            plate_model_path: Path to plate detection model
        """
        self.model_path = plate_model_path
        # In production, load the actual model
        
    def detect_plates(self, frame: np.ndarray, detections: List[Dict]) -> List[Dict]:
        """
        Detect license plates in frame
        
        Args:
            frame: Input frame
            detections: Vehicle detections
            
        Returns:
            List of detected plates with regions
        """
        plates = []
        
        # Filter for vehicle detections
        vehicles = [d for d in detections if d['class_name'] in ['car', 'motorcycle', 'truck', 'bus']]
        
        for vehicle in vehicles:
            # Extract vehicle region
            x1, y1, x2, y2 = [int(v) for v in vehicle['bbox']]
            vehicle_region = frame[y1:y2, x1:x2]
            
            # Detect plate in vehicle region
            plate_bbox = self._detect_plate_in_region(vehicle_region)
            
            if plate_bbox:
                # Convert to frame coordinates
                px1, py1, px2, py2 = plate_bbox
                plate = {
                    'bbox': [x1 + px1, y1 + py1, x1 + px2, y1 + py2],
                    'vehicle_bbox': vehicle['bbox'],
                    'region': vehicle_region[py1:py2, px1:px2],
                    'confidence': vehicle['confidence']
                }
                plates.append(plate)
        
        return plates
    
    @staticmethod
    def _detect_plate_in_region(region: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """
        Detect plate in vehicle region using template matching or edge detection
        
        Args:
            region: Vehicle region of interest
            
        Returns:
            Plate bounding box or None
        """
        if region.shape[0] == 0 or region.shape[1] == 0:
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection
        edges = cv2.Canny(gray, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        
        # Look for rectangular contours (potential plates)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Plate characteristics: wider than tall, reasonable size
            if w > h and w > 30 and h > 15:
                return (x, y, x + w, y + h)
        
        return None
    
    def extract_plate_region(self, frame: np.ndarray, plate_bbox: List[float]) -> np.ndarray:
        """
        Extract plate region from frame
        
        Args:
            frame: Input frame
            plate_bbox: Plate bounding box
            
        Returns:
            Extracted plate region
        """
        x1, y1, x2, y2 = [int(v) for v in plate_bbox]
        return frame[y1:y2, x1:x2]
