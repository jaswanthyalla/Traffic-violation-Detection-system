"""
Violation Logic Module
Determines and records traffic violations
"""
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from database import get_database_manager

class ViolationDetector:
    """Class for detecting and logging traffic violations"""
    
    # Violation types
    VIOLATION_TYPES = {
        'no_helmet': 'Rider without helmet',
        'overloading': 'Vehicle overloaded with riders',
        'no_plate': 'License plate not visible',
        'illegal_parking': 'Illegal parking',
        'traffic_signal': 'Traffic signal violation'
    }
    
    def __init__(self, db_path: str = "database/violations.db"):
        """
        Initialize violation detector
        
        Args:
            db_path: Path to violations database
        """
        self.db = get_database_manager(db_path)
        
    def detect_violations(self, frame_data: Dict) -> List[Dict]:
        """
        Detect violations based on frame analysis
        
        Args:
            frame_data: Dictionary with detection results
                - detections: List of detections
                - helmet_violations: List of helmet violations
                - rider_count: Number of riders
                - plates: Detected plates
                - plate_numbers: Extracted plate numbers
                
        Returns:
            List of detected violations
        """
        violations = []
        
        # Check helmet violations
        if 'helmet_violations' in frame_data:
            for violation in frame_data['helmet_violations']:
                violations.append({
                    'type': 'no_helmet',
                    'description': self.VIOLATION_TYPES['no_helmet'],
                    'confidence': violation.get('confidence', 0),
                    'bbox': violation.get('person_bbox'),
                    'severity': 'high'
                })
        
        # Check rider count (overloading)
        if 'rider_count' in frame_data:
            rider_info = frame_data['rider_count']
            if rider_info['count'] > 2:  # Max 2 riders for bike
                violations.append({
                    'type': 'overloading',
                    'description': f"{self.VIOLATION_TYPES['overloading']} ({rider_info['count']} riders)",
                    'confidence': 0.9,
                    'data': rider_info,
                    'severity': 'medium'
                })
        
        # Check license plate
        if 'plates' in frame_data and len(frame_data['plates']) == 0:
            detections = frame_data.get('detections', [])
            vehicles = [d for d in detections if d.get('class_name') in 
                       ['car', 'motorcycle', 'truck', 'bus']]
            if vehicles:
                violations.append({
                    'type': 'no_plate',
                    'description': self.VIOLATION_TYPES['no_plate'],
                    'confidence': 0.8,
                    'bbox': vehicles[0]['bbox'],
                    'severity': 'high'
                })
        
        return violations
    
    def record_violation(self, violation: Dict, screenshot_path: Optional[str] = None) -> int:
        """
        Record violation to database
        
        Args:
            violation: Violation dictionary
            screenshot_path: Path to violation screenshot
            
        Returns:
            Violation ID
        """
        if screenshot_path is not None:
            violation['screenshot_path'] = screenshot_path
        return self.db.record_violation(violation)
    
    def get_recent_violations(self, limit: int = 50) -> List[Dict]:
        """
        Get recent violations from database
        
        Args:
            limit: Number of recent violations to retrieve
            
        Returns:
            List of violation records
        """
        return self.db.get_recent_violations(limit)
    
    def update_violation_status(self, violation_id: int, status: str) -> bool:
        """
        Update violation status
        
        Args:
            violation_id: ID of violation
            status: New status (pending, processed, dismissed, etc.)
            
        Returns:
            True if successful
        """
        return self.db.update_violation_status(violation_id, status)
