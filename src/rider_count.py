"""
Rider Count Module
Counts number of riders on a vehicle
"""
import numpy as np
from typing import List, Dict, Tuple

class RiderCounter:
    """Class for counting riders on a vehicle"""
    
    def __init__(self):
        """Initialize rider counter"""
        self.min_person_height = 50
        self.person_overlap_threshold = 0.3
        
    def count_riders(self, detections: List[Dict]) -> Dict:
        """
        Count number of riders detected
        
        Args:
            detections: List of all detections
            
        Returns:
            Dictionary with rider count and details
        """
        person_dets = [d for d in detections if d['class_name'] == 'person']
        
        # Filter out detections that are too small (likely false positives)
        valid_persons = [p for p in person_dets 
                        if self._get_bbox_height(p['bbox']) >= self.min_person_height]
        
        # Remove overlapping detections (likely same person detected multiple times)
        filtered_persons = self._remove_overlapping_detections(valid_persons)
        
        return {
            'count': len(filtered_persons),
            'detections': filtered_persons,
            'raw_count': len(person_dets),
            'filtered_out': len(person_dets) - len(filtered_persons)
        }
    
    @staticmethod
    def _get_bbox_height(bbox: List[float]) -> float:
        """Get height of bounding box"""
        x1, y1, x2, y2 = bbox
        return y2 - y1
    
    def _remove_overlapping_detections(self, detections: List[Dict]) -> List[Dict]:
        """
        Remove overlapping detections (same person detected multiple times)
        
        Args:
            detections: List of detections
            
        Returns:
            Filtered list of detections
        """
        if not detections:
            return []
        
        filtered = []
        used = set()
        
        # Sort by confidence (highest first)
        sorted_dets = sorted(detections, key=lambda x: x['confidence'], reverse=True)
        
        for i, det in enumerate(sorted_dets):
            if i in used:
                continue
            
            filtered.append(det)
            
            # Mark overlapping detections as used
            for j in range(i + 1, len(sorted_dets)):
                if j in used:
                    continue
                
                iou = self._calculate_iou(det['bbox'], sorted_dets[j]['bbox'])
                if iou > self.person_overlap_threshold:
                    used.add(j)
        
        return filtered
    
    @staticmethod
    def _calculate_iou(box1: List[float], box2: List[float]) -> float:
        """Calculate Intersection over Union"""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # Intersection
        xi1 = max(x1_1, x1_2)
        yi1 = max(y1_1, y1_2)
        xi2 = min(x2_1, x2_2)
        yi2 = min(y2_1, y2_2)
        
        if xi2 < xi1 or yi2 < yi1:
            return 0.0
        
        intersection = (xi2 - xi1) * (yi2 - yi1)
        
        # Union
        box1_area = (x2_1 - x1_1) * (y2_1 - y1_1)
        box2_area = (x2_2 - x1_2) * (y2_2 - y1_2)
        union = box1_area + box2_area - intersection
        
        return intersection / union if union > 0 else 0
    
    def check_overloading(self, rider_count: int, max_riders: int = 2) -> bool:
        """
        Check if vehicle is overloaded with riders
        
        Args:
            rider_count: Number of riders detected
            max_riders: Maximum allowed riders
            
        Returns:
            True if overloading violation detected
        """
        return rider_count > max_riders
