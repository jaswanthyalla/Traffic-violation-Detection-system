"""
Traffic Violation Detection System
Reusable detection engine for offline + online modes
"""

import cv2
import os
import time
from datetime import datetime
import logging

# -------------------------------------------------
# SAFE IMPORTS
# -------------------------------------------------
try:
    from detection import ObjectDetector
    from helmet_check import HelmetChecker
    from rider_count import RiderCounter
    from plate_detection import PlateDetector
    from ocr_reader import OCRReader
    from violation_logic import ViolationDetector
except ImportError:
    from src.detection import ObjectDetector
    from src.helmet_check import HelmetChecker
    from src.rider_count import RiderCounter
    from src.plate_detection import PlateDetector
    from src.ocr_reader import OCRReader
    from src.violation_logic import ViolationDetector

logger = logging.getLogger(__name__)


class TrafficViolationDetectionSystem:
    """
    Core Detection Engine

    Used by:
    - app.py  (testing)
    - web_app.py (dashboard)
    """

    def __init__(self, config: dict):

        # ---------------- CONFIG ----------------
        self.capture_mode = config.get("capture_mode", "offline")
        self.video_path = config.get("video_path")
        url = config.get("stream_url", 0)
        if isinstance(url, str) and url.isdigit():
            url = int(url)
        self.stream_url = url

        self.output_dir = config.get("output_dir", "output")
        self.confidence_threshold = config.get("confidence_threshold", 0.45)

        self.running = True

        # ---------------- DIRECTORIES ----------------
        self.screenshot_dir = os.path.join(self.output_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)

        # ---------------- MODELS ----------------
        self.detector = ObjectDetector(
            config.get("detection_model", "yolov8n.pt")
        )
        self.detector.set_confidence_threshold(self.confidence_threshold)

        self.helmet_checker = HelmetChecker(
            config.get("helmet_model", "models/yolo_helmet.pt")
        )

        self.rider_counter = RiderCounter()

        self.plate_detector = PlateDetector(
            config.get("plate_model", "models/yolo_plate.pt")
        )

        self.ocr_reader = OCRReader()

        self.violation_detector = ViolationDetector(
            config.get("database_path", "database/violations.db")
        )

        # ---------------- STATE ----------------
        self.violations = []
        self.last_violation_time = {}
        self.violation_cooldown = 5  # seconds

    # ==================================================
    # START DETECTION
    # ==================================================
    def run(self, display=False):

        if self.capture_mode == "online":
            cap = cv2.VideoCapture(self.stream_url)
            logger.info("🔴 ONLINE MODE STARTED")
        else:
            cap = cv2.VideoCapture(self.video_path)
            logger.info("📼 OFFLINE MODE STARTED")

        if not cap.isOpened():
            logger.error("❌ Cannot open video source")
            return {"total_frames": 0, "violations": []}

        frame_count = 0

        while self.running:

            ret, frame = cap.read()
            if not ret:
                break

            frame_count += 1
            self.process_frame(frame, frame_count)

            if display:
                cv2.imshow("Traffic Detection", frame)
                if cv2.waitKey(1) & 0xFF == 27:
                    break

        cap.release()
        cv2.destroyAllWindows()

        return {
            "total_frames": frame_count,
            "violations": self.violations
        }

    # ==================================================
    # STOP FROM WEB
    # ==================================================
    def stop(self):
        self.running = False
        logger.info("🛑 Detection stopped")

    # ==================================================
    # PROCESS FRAME
    # ==================================================
    def process_frame(self, frame, frame_number):
        detections = self.detector.detect(frame)
        if not detections:
            return None
        helmet_violations = self.helmet_checker.check_helmet(detections, frame.shape)
        rider_info = self.rider_counter.count_riders(detections)

        plates = self.plate_detector.detect_plates(frame, detections)
        plate_numbers = []

        for plate in plates:
            region = plate.get("region")
            if region is not None:
                text = self.ocr_reader.read_plate(region)
                if text:
                    plate["number"] = text
                    plate_numbers.append(text)

        frame_data = {
        "detections": detections,
        "helmet_violations": helmet_violations,
        "rider_count": rider_info,
        "plates": plates,
        "plate_numbers": plate_numbers
        }

        new_violations = self.violation_detector.detect_violations(frame_data)

        now = time.time()
        detected_violation = None

        for v in new_violations:

            plate_num = plate_numbers[0] if plate_numbers else f"unknown_{frame_number//30}"

            key = f"{v['type']}_{plate_num}"

            last = self.last_violation_time.get(plate_num, 0)
            if now - last < self.violation_cooldown:
                continue

            self.last_violation_time[plate_num] = now

            v["plate_number"] = plate_num
            v["frame"] = frame_number

            # FINE GENERATION
            if v['type'] == 'no_helmet':
                v['fine_amount'] = 1000.0
            elif v['type'] == 'overloading':
                v['fine_amount'] = 2000.0
            elif v['type'] == 'mobile_usage':
                v['fine_amount'] = 5000.0
            else:
                v['fine_amount'] = 500.0

            filenames = self.save_violation_screenshot(
                frame, v, plate_num, frame_data)

            v["screenshot_path"] = filenames.get("bike_photo")
            v["plate_screenshot_path"] = filenames.get("plate_photo")

            self.violation_detector.record_violation(v)
            self.violations.append(v)

            detected_violation = {
                "type": v["type"],
                "plate": plate_num,
                "fine_amount": v["fine_amount"],
                "bike_filename": filenames.get("bike_photo"),
                "plate_filename": filenames.get("plate_photo")
            }

        return detected_violation
    # ==================================================
    # SAVE SCREENSHOT
    # ==================================================
    # ==================================================
    # SAVE SCREENSHOT
    # ==================================================
    def save_violation_screenshot(self, frame, violation, plate_number, frame_data=None):

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean plate number for filename
        safe_plate = "".join(c for c in plate_number if c.isalnum())
        if not safe_plate:
            safe_plate = "unknown"

        bike_filename = f"{violation['type']}_{safe_plate}_{timestamp}_bike.jpg"
        plate_filename = f"{violation['type']}_{safe_plate}_{timestamp}_plate.jpg"
        
        bike_filepath = os.path.join(self.screenshot_dir, bike_filename)
        plate_filepath = os.path.join(self.screenshot_dir, plate_filename)

        annotated = frame.copy()
        
        # 1. SAVE PLATE PHOTO
        plate_saved = False
        if frame_data and "plates" in frame_data and len(frame_data["plates"]) > 0:
            plate_box = frame_data["plates"][0].get("bbox")
            if plate_box:
                px1, py1, px2, py2 = map(int, plate_box)
                # Add tiny padding to plate
                ph, pw = frame.shape[:2]
                px1 = max(0, px1 - 10)
                py1 = max(0, py1 - 10)
                px2 = min(pw, px2 + 10)
                py2 = min(ph, py2 + 10)
                
                plate_crop = frame[py1:py2, px1:px2]
                if plate_crop.size > 0:
                    cv2.imwrite(plate_filepath, plate_crop)
                    plate_saved = True

        # 2. DRAW BOUNDING BOX ON BIKE
        if violation.get("bbox"):
            x1, y1, x2, y2 = map(int, violation["bbox"])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)

            label = f"{violation['type']} | {plate_number}"
            cv2.putText(
                annotated,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2,
                cv2.LINE_AA,
            )

        # 3. CROP THE BIKE PHOTO
        if frame_data and "detections" in frame_data:
            motorcycles = [d for d in frame_data["detections"] if d.get("class_name") in ["motorcycle", "bicycle"]]
            if motorcycles:
                # Find the largest motorcycle detection
                best_bike = max(motorcycles, key=lambda m: (m['bbox'][2]-m['bbox'][0]) * (m['bbox'][3]-m['bbox'][1]))
                bx1, by1, bx2, by2 = map(int, best_bike["bbox"])
                
                # Add 60px padding around the bike
                pad = 60
                h, w = frame.shape[:2]
                crop_y1 = max(0, by1 - pad)
                crop_y2 = min(h, by2 + pad)
                crop_x1 = max(0, bx1 - pad)
                crop_x2 = min(w, bx2 + pad)
                
                annotated = annotated[crop_y1:crop_y2, crop_x1:crop_x2]

        # Save bike screenshot
        cv2.imwrite(bike_filepath, annotated)

        return {
            "bike_photo": bike_filename,
            "plate_photo": plate_filename if plate_saved else None
        }

