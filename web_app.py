"""
Web Dashboard Application
Traffic Violation Detection Dashboard
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import threading
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
import yaml
import cv2
from twilio.rest import Client
import time


# -------------------------------------------------
# PATH SETUP
# -------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

from database import get_database_manager
from detection_system import TrafficViolationDetectionSystem

# -------------------------------------------------
# FLASK SETUP
# -------------------------------------------------
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "videos")
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("output/screenshots", exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = get_database_manager("database/violations.db")
print("WEB APP DB:", db.db_path)
processing_status = {}

from flask import Response
def generate_frames():
    global latest_frame, camera_running

    while True:
        if not camera_running or latest_frame is None:
            time.sleep(0.1)
            continue

        frame = latest_frame.copy()
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# CAMERA GLOBALS
camera = None
camera_running = False
camera_thread = None
latest_frame = None
# CONFIG
def load_config():
    if os.path.exists("config.yaml"):
        with open("config.yaml") as f:
            return yaml.safe_load(f) or {}
    return {}

config = load_config()
capture_mode = config.get("capture_mode", "offline")


# UTILS

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
# ---------------- CALL SYSTEM ----------------

ACCOUNT_SID = "AC1426e6628f8d8b8a2fe9bf0104d1d466"
AUTH_TOKEN = "cf640cd8008d49bf6e7c2d02eedb72b1"
TWILIO_NUMBER = "+17178640924"

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def make_call(phone, message):
    try:
        client.calls.create(
            to=phone,
            from_=TWILIO_NUMBER,
            twiml=f'<Response><Say>{message}</Say></Response>'
        )
        print("📞 Call sent to", phone)
    except Exception as e:
        print("Call error:", e)

def send_sms_with_proof(phone, vehicle, v_type, filename):
    try:
        # NOTE: Twilio requires a public URL to send photos via MMS. 
        # If you use ngrok (e.g., https://1234.ngrok-free.app), you can pass the media_url to attach the photo!
        # public_image_url = f"https://YOUR-PUBLIC-NGROK-URL.ngrok-free.app/api/screenshot/{filename}"
        
        msg_body = f"Traffic Violation Notice: Your vehicle {vehicle} was detected with a {v_type} violation. Please pay the fine immediately."
        
        client.messages.create(
            to=phone,
            from_=TWILIO_NUMBER,
            body=msg_body
            # media_url=[public_image_url]  # Uncomment when you have a public URL
        )
        print("✉️ SMS sent to", phone)
    except Exception as e:
        print("SMS error:", e)


def get_voice_message(violation, vehicle):
    if violation == "no_helmet":
        return f"Attention. Your vehicle {vehicle} has been detected with a no helmet violation. Meeru helmet pettukoledu. Dayachesi helmet vadandi."
    elif violation == "overloading":
        return f"Attention. Your vehicle {vehicle} has been detected with an overloading violation. Mee vehicle lo ekkuva mandi unnaru. Overloading cheyakandi."
    elif violation == "mobile_usage":
        return f"Attention. Your vehicle {vehicle} has been detected with a mobile usage violation. Driving chesthu mobile vadakandi."
    else:
        return f"Traffic violation detected for vehicle {vehicle}."
last_called = {}

def can_call(vehicle):
    now = time.time()
    if vehicle not in last_called or now - last_called[vehicle] > 86400:
        last_called[vehicle] = now
        return True
    return False
# CAMERA LOOP
def initialize_camera():
    global camera
    if camera is None:
        stream_url = config.get("stream_url")
        source = stream_url if stream_url is not None else config.get("webcam_device", 0)
        camera = cv2.VideoCapture(source)


def camera_capture_loop():
    global camera, camera_running, latest_frame

    initialize_camera()
    camera_running = True

    system = TrafficViolationDetectionSystem({
        "output_dir": "output",
        "confidence_threshold": config.get("confidence_threshold", 0.45)
    })
    
    frame_count = 0

    while camera_running:
        ret, frame = camera.read()
        if not ret:
            break
            
        frame_count += 1
        latest_frame = frame

        try:
            violation = system.process_frame(frame, frame_count)
        except Exception as e:
            logger.error(f"Detection error: {e}")
            violation = None
        if violation:
            try:
               # vehicle=violation.get("plate_number",violation.get("plate","unknown"))
                #v_type = violation.get("type","unknown")


                # 🔥 TEST MODE: Hardcoding the dummy plate and default violation
                vehicle = "AP30ak5566"
                v_type = violation.get("type", "no_helmet") if hasattr(violation, 'get') else "no_helmet"

                if vehicle == "unknown":
                    print("❌ Plate not detected")
                    continue

                # Get owner from DB
                owner = None
                if hasattr(db, 'get_owner'):
                    owner = db.get_owner(vehicle)
                    print(f"DEBUG: get_owner called for {vehicle}, returned {owner}")
                else:
                    print(f"DEBUG: db object DOES NOT have get_owner method! It has: {dir(db)}")

                # ❌ OWNER NOT FOUND
                if not owner:
                    print(f"No owner found for vehicle: {vehicle}")
                    continue

                # ❌ PHONE NOT FOUND
                if not owner.get("phone"):
                    print(f" No phone number for vehicle: {vehicle}")
                    continue

                # ✅ CALL ONLY IF EVERYTHING OK
                if can_call(vehicle):
                    msg = get_voice_message(v_type, vehicle)
                    filename = violation.get("filename", "")
                    print(f"📞 Calling {owner['phone']} for {vehicle}")

                    # Thread for the call
                    threading.Thread(
                        target=make_call,
                        args=(owner["phone"], msg),
                        daemon=True
                    ).start()
                    
                    # Thread for the SMS / Proof
                    threading.Thread(
                        target=send_sms_with_proof,
                        args=(owner["phone"], vehicle, v_type, filename),
                        daemon=True
                    ).start()

            except Exception as e:
                logger.error(f"Error in Twilio call logic: {e}")
        # 🔥 DISPLAY (optional)
        # cv2.imshow("🚦 Traffic Detection Live", frame)

        # if cv2.waitKey(1) & 0xFF == 27:
        #     break

    # ✅ CLEANUP
    if camera:
        camera.release()
        camera = None
    cv2.destroyAllWindows()
    latest_frame = None
    camera_running = False
# -------------------------------------------------
# VIDEO PROCESSING (OFFLINE)
# -------------------------------------------------
def process_video(video_path, video_id):
    try:
        processing_status[video_id] = {
            "status": "processing",
            "progress": 0,
            "message": "Processing started"
        }

        system = TrafficViolationDetectionSystem({
            "video_path": video_path,
            "output_dir": "output",
            "confidence_threshold": config.get("confidence_threshold", 0.45)
        })

        stats = system.run(display=False)

        processing_status[video_id] = {
            "status": "completed",
            "progress": 100,
            "message": f"Completed. {len(stats.get('violations', []))} violations found"
        }

    except Exception as e:
        logger.error(e, exc_info=True)
        processing_status[video_id] = {
            "status": "error",
            "progress": 0,
            "message": str(e)
        }

# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')
@app.route("/")
def index():
    return render_template("dashboard.html")

# ---------------- CONFIG --------------------------
@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify(success=True, config={
        "capture_mode": capture_mode,
        "stream_url": config.get("stream_url"),
        "webcam_device": config.get("webcam_device", 0)
    })

@app.route("/api/config", methods=["PUT"])
def update_config():
    global capture_mode, config, camera_running
    data = request.json

    if "capture_mode" in data:
        capture_mode = data["capture_mode"]
        config["capture_mode"] = capture_mode
    if "stream_url" in data:
        # Save as null if string is empty
        val = data["stream_url"].strip() if data["stream_url"] else None
        config["stream_url"] = val if val else None
    if "webcam_device" in data:
        config["webcam_device"] = int(data["webcam_device"])

    with open("config.yaml", "w") as f:
        yaml.dump(config, f)

    return jsonify(success=True)

# ---------------- OFFLINE VIDEO -------------------
@app.route("/api/videos/upload", methods=["POST"])
def upload_video():
    if capture_mode != "offline":
        return jsonify(success=False, error="Switch to Offline mode")

    if "file" not in request.files:
        return jsonify(success=False, error="No file")

    file = request.files["file"]

    if file.filename == "":
        return jsonify(success=False, error="Empty filename")

    if not allowed_file(file.filename):
        return jsonify(success=False, error="Invalid file type")

    filename = datetime.now().strftime("%Y%m%d_%H%M%S_") + secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    file.save(filepath)

    video_id = filename.replace(".", "_")

    threading.Thread(
        target=process_video,
        args=(filepath, video_id),
        daemon=True
    ).start()

    return jsonify(success=True, video_id=video_id)

# ---------------- CAMERA ONLINE -------------------
PID_FILE = "camera.pid"

@app.route("/api/camera/start", methods=["POST"])
def start_camera():
    global camera_thread, camera_running

    if camera_running:
        return jsonify(success=False, error="Camera already running")

    camera_thread = threading.Thread(target=camera_capture_loop)
    camera_thread.start()

    return jsonify(success=True, message="Camera started")

@app.route("/api/camera/stop", methods=["POST"])
def stop_camera():
    global camera_running

    camera_running = False

    return jsonify(success=True, message="Camera stopped")
# ---------------- SCREENSHOTS ---------------------
@app.route("/api/screenshots")
def screenshots():
    folder = "output/screenshots"
    shots = []

    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.lower().endswith((".jpg", ".png")):
                path = os.path.join(folder, f)
                shots.append({
                    "filename": f,
                    "url": f"/api/screenshot/{f}",
                    "timestamp": datetime.fromtimestamp(os.path.getmtime(path)).isoformat()
                })

    return jsonify(success=True, screenshots=shots)

@app.route("/api/screenshot/<filename>")
def screenshot(filename):
    path = os.path.join("output/screenshots", filename)
    if not os.path.exists(path):
        return jsonify(success=False, error="Not found"), 404
    return send_file(path, mimetype="image/jpeg")

@app.route("/api/screenshot/<filename>", methods=["DELETE"])
def delete_screenshot(filename):
    try:
        path = os.path.join("output/screenshots", filename)
        if os.path.exists(path):
            os.remove(path)
            return jsonify(success=True, message="Deleted")
        return jsonify(success=False, error="Not found"), 404
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

# ---------------- STATUS --------------------------
@app.route("/api/video/status/<video_id>")
def video_status(video_id):
    status = processing_status.get(video_id)
    if not status:
        return jsonify(success=False, error="Video ID not found"), 404
    return jsonify(success=True, status=status)

# ---------------- VIOLATIONS ----------------------
@app.route("/api/violations")
def get_violations():
    try:
        limit = int(request.args.get("limit", 50))
        violations = db.get_recent_violations(limit=limit)
        return jsonify(success=True, violations=violations)
    except Exception as e:
        logger.error(f"Error fetching violations: {e}")
        return jsonify(success=False, error=str(e)), 500

# ---------------- STATS ---------------------------
@app.route("/api/stats")
def get_stats():
    try:
        # Simple stats calculation
        violations = db.get_recent_violations(limit=1000)
        total = len(violations)
        
        # Count last 24h
        now = datetime.now()
        last_24h = 0
        for v in violations:
            try:
                ts_str = str(v['timestamp']).replace(" ", "T")
                ts = datetime.fromisoformat(ts_str)
                if (now - ts).total_seconds() < 86400:
                    last_24h += 1
            except (ValueError, TypeError):
                continue
        
        # Count types
        helmet = sum(1 for v in violations if v['violation_type'] == 'no_helmet')
        overload = sum(1 for v in violations if v['violation_type'] == 'overloading')
        
        return jsonify(success=True, stats={
            "total": total,
            "last_24h": last_24h,
            "helmet": helmet,
            "overloading": overload # Match JS property name if needed, JS uses 'overloading' or 'overload'?
                                    # JS: document.getElementById("stat-overload").textContent
        })
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return jsonify(success=False, error=str(e)), 500

# -------------------------------------------------
# MAIN
# -------------------------------------------------
if __name__ == "__main__":
    print("🚦 Traffic Violation Dashboard Running")
    print("👉 http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)
