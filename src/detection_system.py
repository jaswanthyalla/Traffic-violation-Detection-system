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
        self.stream_url = config.get("stream_url", 0)

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

            filename = self.save_violation_screenshot(
                frame, v, plate_num)

            v["screenshot_path"] = filename

            self.violation_detector.record_violation(v)
            self.violations.append(v)

            detected_violation = {
            "type": v["type"],
            "plate": plate_num,
            "filename": os.path.basename(filename)
            }

        return detected_violation
    # ==================================================
    # SAVE SCREENSHOT
    # ==================================================
    # ==================================================
    # SAVE SCREENSHOT
    # ==================================================
    def save_violation_screenshot(self, frame, violation, plate_number):

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Clean plate number for filename
        safe_plate = "".join(c for c in plate_number if c.isalnum())
        if not safe_plate:
            safe_plate = "unknown"

        filename = f"{violation['type']}_{safe_plate}_{timestamp}.jpg"
        filepath = os.path.join(self.screenshot_dir, filename)

        annotated = frame.copy()

        # Draw bounding box if available
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

        # Save screenshot
        cv2.imwrite(filepath, annotated)

        return filepath

