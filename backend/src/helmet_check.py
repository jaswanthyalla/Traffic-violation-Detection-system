"""
Helmet Detection Module
Checks if riders are wearing helmets
"""
import numpy as np
from typing import List, Dict

class HelmetChecker:
    """Class for checking helmet compliance"""
    
    def __init__(self, helmet_model_path: str = "models/yolo_helmet.pt"):
        """
        Initialize helmet checker
        
        Args:
            helmet_model_path: Path to helmet detection model
        """
        self.model_path = helmet_model_path
        # In production, load the actual model
        
    def check_helmet(self, detections: List[Dict], frame_shape: tuple) -> List[Dict]:
        """
        Check if detected riders are wearing helmets
        
        Args:
            detections: List of detected objects
            frame_shape: Shape of the frame
            
        Returns:
            List of violations (riders without helmets)
        """
        violations = []
        
        # Filter for person detections (class 0 in COCO)
        person_dets = [d for d in detections if d['class_name'] == 'person']
        
        for person in person_dets:
            # Check if helmet is detected near person
            helmet_detected = self._detect_helmet_on_person(person, detections)
            
            if not helmet_detected:
                violations.append({
                    'type': 'no_helmet',
                    'person_bbox': person['bbox'],
                    'center': person['center'],
                    'confidence': person['confidence']
                })
        
        return violations
    
    @staticmethod
    def _detect_helmet_on_person(person: Dict, all_detections: List[Dict]) -> bool:
        """
        Check if helmet is detected near person
        
        Args:
            person: Person detection
            all_detections: All detections in frame
            
        Returns:
            True if helmet detected near person
        """
        # Filter for helmet detections
        helmet_dets = [d for d in all_detections if 'helmet' in d['class_name'].lower()]
        
        if not helmet_dets:
            return False
        
        person_bbox = person['bbox']
        person_center = person['center']
        
        # Check if helmet is above person's head (in bounding box)
        for helmet in helmet_dets:
            helmet_center = helmet['center']
            # Simple distance check - helmet should be near person's head area
            distance = ((helmet_center[0] - person_center[0])**2 + 
                       (helmet_center[1] - person_center[1])**2)**0.5
            
            if distance < 100:  # Threshold can be tuned
                return True
        
        return False
    
    def is_violation(self, detections: List[Dict]) -> bool:
        """Check if there's a helmet violation"""
        violations = self.check_helmet(detections, None)
        return len(violations) > 0
