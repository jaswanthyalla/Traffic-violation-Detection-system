"""
Main Detection Application
Coordinates detection pipeline and database storage
"""
import cv2
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import yaml

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from video_reader import VideoReader
from detection import ObjectDetector
from helmet_check import HelmetChecker
from rider_count import RiderCounter
from plate_detection import PlateDetector
from ocr_reader import OCRReader
from violation_logic import ViolationDetector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('output/logs/detection.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TrafficViolationDetectionSystem:
    """Main detection system class"""
    
    def __init__(self, config: dict = None):
        """
        Initialize detection system
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._load_default_config()
        
        # Initialize components
        logger.info("Initializing detection system...")
        self.video_reader = VideoReader(self.config.get('video_path'))
        self.object_detector = ObjectDetector(self.config.get('detection_model'))
        self.helmet_checker = HelmetChecker(self.config.get('helmet_model'))
        self.rider_counter = RiderCounter()
        self.plate_detector = PlateDetector(self.config.get('plate_model'))
        self.ocr_reader = OCRReader()
        self.violation_detector = ViolationDetector(self.config.get('database_path'))
        
        self.frame_count = 0
        self.violation_count = 0
        self.last_violation_time = {}  # Track last violation time per plate
        self.violation_cooldown = 30  # Don't record same plate twice in 30 seconds
        
    def _load_default_config(self) -> dict:
        """Load default configuration"""
        return {
            'video_path': 'data/videos/traffic_sample.mp4',
            'detection_model': 'yolov8n.pt',
            'helmet_model': 'models/yolo_helmet.pt',
            'plate_model': 'models/yolo_plate.pt',
            'database_path': 'database/violations.db',
            'output_dir': 'output',
            'screenshot_interval': 5,
            'confidence_threshold': 0.45
        }
    
    def run(self, max_frames: int = None, display: bool = False) -> dict:
        """
        Run detection system on video
        
        Args:
            max_frames: Maximum frames to process (None for all)
            display: Whether to display video with annotations
            
        Returns:
            Statistics dictionary
        """
        logger.info("Starting detection run...")
        
        # Open video source
        if not self.video_reader.open():
            logger.error("Failed to open video source")
            return {'success': False}
        
        props = self.video_reader.get_properties()
        logger.info(f"Video properties: {props}")
        
        # Prepare output video writer
        output_path = os.path.join(self.config['output_dir'], 'detection_output.mp4')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, props['fps'], 
                             (props['width'], props['height']))
        
        stats = {
            'total_frames': 0,
            'violations': [],
            'output_video': output_path
        }
        
        try:
            while True:
                ret, frame = self.video_reader.read_frame()
                
                if not ret:
                    break
                
                self.frame_count += 1
                
                # Process frame
                frame_violations = self._process_frame(frame)
                stats['violations'].extend(frame_violations)
                
                # Annotate frame
                annotated_frame = self._annotate_frame(frame, frame_violations)
                out.write(annotated_frame)
                
                if display:
                    cv2.imshow('Detection', annotated_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if max_frames and self.frame_count >= max_frames:
                    break
                
                if self.frame_count % 30 == 0:
                    logger.info(f"Processed {self.frame_count} frames, "
                              f"Violations: {self.violation_count}")
            
            stats['total_frames'] = self.frame_count
            logger.info(f"Detection completed. Processed {self.frame_count} frames")
            
        except Exception as e:
            logger.error(f"Error during detection: {e}", exc_info=True)
            stats['error'] = str(e)
        
        finally:
            out.release()
            self.video_reader.release()
            if display:
                cv2.destroyAllWindows()
        
        return stats
    
    def _process_frame(self, frame) -> list:
        """
        Process single frame for violations
        
        Args:
            frame: Input frame
            
        Returns:
            List of violations in frame
        """
        violations = []
        
        # Run object detection
        detections = self.object_detector.detect(frame)
        
        if not detections:
            return violations
        
        # Check helmet compliance
        helmet_violations = self.helmet_checker.check_helmet(detections, frame.shape)
        
        # Count riders
        rider_info = self.rider_counter.count_riders(detections)
        
        # Detect license plates
        plates = self.plate_detector.detect_plates(frame, detections)
        
        # Prepare frame data for violation detection
        frame_data = {
            'detections': detections,
            'helmet_violations': helmet_violations,
            'rider_count': rider_info,
            'plates': plates
        }
        
        # Detect violations
        frame_violations = self.violation_detector.detect_violations(frame_data)
        
        # Get current timestamp for duplicate detection
        current_time = datetime.now().timestamp()
        
        # Record violations to database
        for violation in frame_violations:
            # Get license plate for duplicate detection
            plate = violation.get("plate", "unknown")
            
            # Check if we recently recorded a violation for this plate
            last_time = self.last_violation_time.get(plate, 0)
            
            # Skip duplicate violations within cooldown period
            if current_time - last_time < self.violation_cooldown:
                logger.debug(f"Skipping duplicate violation for plate {plate}")
                continue
            
            # Update last violation time for this plate
            self.last_violation_time[plate] = current_time
            
            # Record violation to database
            violation_id = self.violation_detector.record_violation(violation)
            self.violation_count += 1
            
            # Always save screenshot for every violation detected
            screenshot_path = self._save_violation_screenshot(frame, violation)
            if screenshot_path:
                self.violation_detector.update_violation_status(violation_id, 'documented')
            
            violations.append(violation)
        
        return violations
    
    def _save_violation_screenshot(self, frame, violation) -> str:
        """Save screenshot of violation"""
        try:
            screenshot_dir = os.path.join(self.config['output_dir'], 'screenshots')
            os.makedirs(screenshot_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{violation['type']}_{timestamp}.jpg"
            path = os.path.join(screenshot_dir, filename)
            
            cv2.imwrite(path, frame)
            return path
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
            return None
    
    def _annotate_frame(self, frame, violations):
        """Annotate frame with violations"""
        annotated = frame.copy()
        
        # Draw violation count
        violation_text = f"Violations: {len(violations)}"
        cv2.putText(annotated, violation_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Draw violation details
        for i, violation in enumerate(violations):
            y_offset = 60 + (i * 30)
            text = f"{violation['type']}: {violation.get('severity', 'unknown')}"
            cv2.putText(annotated, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            
            # Draw bounding box if available
            if 'bbox' in violation:
                x1, y1, x2, y2 = [int(v) for v in violation['bbox']]
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
        
        return annotated
def process_frame(self, frame):
    frame_violations = self._process_frame(frame)
    annotated_frame = self._annotate_frame(frame, frame_violations)
    return annotated_frame

def main():
    """Main entry point"""
    import yaml
    
    # Load configuration
    config_path = 'config.yaml'
    config = {}
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Loaded config from {config_path}")
    
    # Initialize and run system
    system = TrafficViolationDetectionSystem(config)
    
    # Run indefinitely (max_frames=None) for online mode or full video processing
    stats = system.run(max_frames=None, display=True)
    
    logger.info(f"Detection statistics: {stats}")
    print(f"\nDetection completed!")
    print(f"Total frames: {stats.get('total_frames', 0)}")
    print(f"Total violations: {len(stats.get('violations', []))}")
    print(f"Output video: {stats.get('output_video', 'N/A')}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Traffic Violation Detection System")
    parser.add_argument("--webcam", action="store_true", help="Use webcam for input (overrides config)")
    args = parser.parse_args()
    
    # Load configuration
    config_path = 'config.yaml'
    config = {}
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Loaded config from {config_path}")
    
    # Override config if webcam arg is present
    if args.webcam:
        config['video_path'] = None
        logger.info("Webcam mode enabled via command line argument")
        
    main_system = TrafficViolationDetectionSystem(config)
    
    # Run indefinitely (max_frames=None)
    stats = main_system.run(max_frames=None, display=True)
    
    logger.info(f"Detection statistics: {stats}")
