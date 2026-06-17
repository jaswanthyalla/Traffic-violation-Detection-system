"""
Web Dashboard Application
Traffic Violation Detection Dashboard
"""

from flask import Flask, render_template, jsonify, request, send_file, session, redirect, url_for
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
from flask_cors import CORS
import os
import sys
import threading
import logging
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import yaml
import cv2
from twilio.rest import Client
import time
import numpy as np
import sqlite3

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
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
app = Flask(__name__, 
            template_folder=os.path.join(FRONTEND_DIR, "templates"),
            static_folder=os.path.join(FRONTEND_DIR, "static"))
app.secret_key = "super_secret_tvs_key"
CORS(app)

UPLOAD_FOLDER = os.path.join(BASE_DIR, "data", "videos")
ALLOWED_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("output/screenshots", exist_ok=True)

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/system.log"),
        logging.StreamHandler()
    ]
)
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

def get_twilio_client():
    account_sid = config.get("twilio_account_sid", "AC1426e6628f8d8b8a2fe9bf0104d1d466")
    auth_token = config.get("twilio_auth_token", "cf640cd8008d49bf6e7c2d02eedb72b1")
    return Client(account_sid, auth_token)

def get_twilio_number():
    return config.get("twilio_number", "+17178640924")

def make_call(phone, message):
    try:
        client = get_twilio_client()
        twilio_number = get_twilio_number()
        client.calls.create(
            to=phone,
            from_=twilio_number,
            twiml=f'<Response><Say>{message}</Say></Response>'
        )
        print("📞 Call sent to", phone)
    except Exception as e:
        print("Call error:", e)

def send_sms_with_proof(phone, vehicle, v_type, filename, fine_amount=None):
    try:
        # NOTE: Twilio requires a public URL to send photos via MMS. 
        # If you use ngrok (e.g., https://1234.ngrok-free.app), you can pass the media_url to attach the photo!
        # public_image_url = f"https://YOUR-PUBLIC-NGROK-URL.ngrok-free.app/api/screenshot/{filename}"
        
        fine_text = f" Fine amount: Rs {fine_amount}." if fine_amount else ""
        msg_body = f"Traffic Violation Notice: Your vehicle {vehicle} was detected with a {v_type} violation.{fine_text} Please pay the fine immediately."
        
        client = get_twilio_client()
        twilio_number = get_twilio_number()
        client.messages.create(
            to=phone,
            from_=twilio_number,
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
class CameraReader:
    def __init__(self, source):
        if isinstance(source, int):
            self.cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(source)
            
        self.ret, self.frame = self.cap.read()
        self.running = True
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while self.running:
            if self.cap.isOpened():
                self.ret, self.frame = self.cap.read()
            else:
                time.sleep(0.1)

    def read(self):
        return self.ret, self.frame

    def release(self):
        self.running = False
        self.thread.join(timeout=1.0)
        self.cap.release()

    def isOpened(self):
        return self.cap.isOpened()

def initialize_camera():
    global camera
    if camera is None:
        stream_url = config.get("stream_url")
        source = stream_url if stream_url is not None else config.get("webcam_device", 0)
        if isinstance(source, str):
            source = source.strip()
            if source.isdigit():
                source = int(source)
            elif source.startswith("http") and not source.endswith("/video") and "mjpg" not in source:
                source = source.rstrip("/") + "/video"
                
        camera = CameraReader(source)

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
        if camera is None or not camera.isOpened():
            # Create a placeholder "Offline" frame if camera fails to open
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "CONNECTION FAILED / STREAM OFFLINE", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            latest_frame = blank_frame
            time.sleep(1)
            continue

        ret, frame = camera.read()
        if not ret or frame is None:
            # If stream drops, show offline frame and wait, but don't break loop instantly
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "STREAM DROPPED - RECONNECTING...", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 165, 255), 2)
            latest_frame = blank_frame
            time.sleep(1)
            
            # Try to re-initialize
            camera.release()
            camera = None
            initialize_camera()
            continue
            
        # Resize frame to standard size to prevent large IP camera resolutions from freezing the system
        frame = cv2.resize(frame, (640, 480))
        
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

                phone = owner.get('phone')
                name = owner.get('owner_name')
                fine_amount = violation.get('fine_amount', 0)

                print(f"✅ Found owner: {name} ({phone})")

                # SMS ALERT
                if config.get("twilio_enabled", False) and phone:
                    print("Sending SMS with Twilio...")
                    # Get the bike filename for the SMS attachment placeholder
                    bike_filename = violation.get('bike_filename', violation.get('filename'))
                    send_sms_with_proof(phone, vehicle, v_type, bike_filename, fine_amount)
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

# ---------------- AUTHENTICATION ------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        requested_role = request.form.get('role', 'admin') # From the hidden input
        
        user = db.get_user_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            # Verify the role matches
            if user['role'] != requested_role:
                error_msg = f"Account does not have {requested_role.capitalize()} privileges."
                return render_template('login.html', error=error_msg)
                
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            db.update_last_login(user['id'])
            return redirect(url_for('index'))
            
        return render_template('login.html', error='Invalid username or password')
        
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Verify if user exists
        if db.get_user_by_username(username):
            return render_template('signup.html', error='Username already exists')
            
        hashed_pw = generate_password_hash(password)
        
        # Create user (defaulting to operator role for new signups)
        if db.create_user(username, hashed_pw, name, role='operator'):
            # Automatically log them in after signup
            user = db.get_user_by_username(username)
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['name'] = user['name']
            db.update_last_login(user['id'])
            return redirect(url_for('index'))
        else:
            return render_template('signup.html', error='Failed to create account')
            
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify(success=False, error="Missing required fields")
        
    user = db.get_user_by_username(session['username'])
    if not user or not check_password_hash(user['password_hash'], current_password):
        return jsonify(success=False, error="Incorrect current password")
        
    new_hash = generate_password_hash(new_password)
    if db.update_password(user['id'], new_hash):
        return jsonify(success=True, message="Password updated successfully")
    else:
        return jsonify(success=False, error="Failed to update password")
@app.route("/")
@login_required
def index():
    return render_template("dashboard.html")

@app.route("/violations")
@login_required
def violations_page():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template("violations.html")

@app.route("/live-capture")
@login_required
def live_capture_page():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template("live_capture.html")

@app.route("/analytics")
@login_required
def analytics_page():
    return render_template("analytics.html")

@app.route("/reports")
@login_required
def reports_page():
    return render_template("reports.html")

@app.route("/devices")
@login_required
def devices_page():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template("devices.html")

@app.route("/settings")
@login_required
def settings_page():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template("settings.html")

@app.route("/users")
@login_required
def users_page():
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    users = db.get_all_users()
    return render_template("users.html", users=users)

@app.route("/alerts")
@login_required
def alerts_page():
    return render_template("alerts.html")

@app.route("/logs")
@login_required
def logs_page():
    return render_template("logs.html")

# ---------------- EXPORT --------------------------
@app.route("/api/export/csv")
def export_csv():
    try:
        status_filter = request.args.get("status")
        
        conn = db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT v.*, o.owner_name, o.phone FROM violations v LEFT JOIN owners o ON v.plate_number = o.plate_number"
        params = []
        if status_filter:
            query += " WHERE v.status = ?"
            params.append(status_filter)
            
        query += " ORDER BY v.timestamp DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        import csv
        from io import StringIO
        
        si = StringIO()
        writer = csv.writer(si)
        
        # Write headers
        writer.writerow(['ID', 'Timestamp', 'Plate Number', 'Owner', 'Phone', 'Violation Type', 'Fine Amount', 'Status'])
        
        for r in rows:
            writer.writerow([
                r['id'],
                r['timestamp'],
                r['plate_number'],
                r['owner_name'] or 'Unknown',
                r['phone'] or 'N/A',
                r['violation_type'],
                r['fine_amount'] or 0.0,
                r['status']
            ])
            
        output = si.getvalue()
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=violations_report_{status_filter or 'all'}.csv"}
        )
    except Exception as e:
        return str(e), 500

# ---------------- DEVICES -------------------------
@app.route("/api/devices", methods=["GET"])
@login_required
def get_devices():
    devices = db.get_devices()
    return jsonify(success=True, devices=devices)

@app.route("/api/devices", methods=["POST"])
@login_required
def add_device():
    data = request.json
    name = data.get("name")
    ip_address = data.get("ip_address")
    resolution = data.get("resolution", "1080p")
    
    if not name or not ip_address:
        return jsonify(success=False, error="Name and IP Address are required"), 400
        
    if db.add_device(name, ip_address, resolution):
        return jsonify(success=True)
    return jsonify(success=False, error="Failed to add device"), 500

@app.route("/api/devices/<int:device_id>", methods=["DELETE"])
@login_required
def delete_device(device_id):
    if db.delete_device(device_id):
        return jsonify(success=True)
    return jsonify(success=False, error="Failed to delete device"), 500

@app.route("/api/violations/<int:violation_id>/pay", methods=["POST"])
@login_required
def pay_violation(violation_id):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE violations SET status = 'paid' WHERE id = ?", (violation_id,))
        conn.commit()
        conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e)), 500

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
        val = data["stream_url"]
        if isinstance(val, str):
            val = val.strip()
            if val.isdigit():
                val = int(val)
        config["stream_url"] = val if val is not None and val != "" else None
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

@app.route("/api/logs")
@login_required
def get_logs():
    try:
        log_file = "logs/system.log"
        if not os.path.exists(log_file):
            return jsonify(success=True, logs=[])
            
        with open(log_file, "r") as f:
            lines = f.readlines()
            
        # Get last 100 lines
        recent_lines = lines[-100:]
        return jsonify(success=True, logs=recent_lines)
    except Exception as e:
        return jsonify(success=False, error=str(e))

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
        violations = db.get_recent_violations(limit=1000)
        total = len(violations)
        
        now = datetime.now()
        last_24h = 0
        
        trend = [0] * 7
        finance_trend_paid = [0] * 7
        finance_trend_pending = [0] * 7
        labels = []
        for i in range(6, -1, -1):
            labels.append((now - timedelta(days=i)).strftime("%a"))
            
        finance_trend_weekly_paid = [0] * 4
        finance_trend_weekly_pending = [0] * 4
        weekly_labels = []
        for i in range(3, -1, -1):
            weekly_labels.append((now - timedelta(days=i*7)).strftime("%b %d"))
            
        finance_trend_monthly_paid = [0] * 6
        finance_trend_monthly_pending = [0] * 6
        monthly_labels = []
        for i in range(5, -1, -1):
            monthly_labels.append((now - timedelta(days=i*30)).strftime("%b"))

        types_count = {"no_helmet": 0, "overloading": 0, "no_plate": 0}
        revenue_by_category = {}
        
        for v in violations:
            try:
                ts_str = str(v['timestamp']).replace(" ", "T")
                ts = datetime.fromisoformat(ts_str)
                
                if (now - ts).total_seconds() < 86400:
                    last_24h += 1
                
                days_ago = (now.date() - ts.date()).days
                
                # Daily
                if 0 <= days_ago <= 6:
                    trend[6 - days_ago] += 1
                    if v.get('status') == 'paid':
                        finance_trend_paid[6 - days_ago] += 1
                    else:
                        finance_trend_pending[6 - days_ago] += 1
                        
                # Weekly (last 4 weeks = 28 days)
                if 0 <= days_ago < 28:
                    week_idx = 3 - (days_ago // 7)
                    if v.get('status') == 'paid':
                        finance_trend_weekly_paid[week_idx] += 1
                    else:
                        finance_trend_weekly_pending[week_idx] += 1
                        
                # Monthly (last 6 months approx = 180 days)
                if 0 <= days_ago < 180:
                    month_idx = 5 - (days_ago // 30)
                    if v.get('status') == 'paid':
                        finance_trend_monthly_paid[month_idx] += 1
                    else:
                        finance_trend_monthly_pending[month_idx] += 1
                    
                v_type = v['violation_type']
                if v_type in types_count:
                    types_count[v_type] += 1
                else:
                    types_count[v_type] = 1
                    
                # Add to revenue if paid
                if v.get('status') == 'paid':
                    fine_amount = v.get('fine_amount', 0)
                    if fine_amount:
                        revenue_by_category[v_type] = revenue_by_category.get(v_type, 0) + fine_amount
                    
            except (ValueError, TypeError):
                continue
        
        return jsonify(success=True, stats={
            "total": total,
            "last_24h": last_24h,
            "helmet": types_count.get("no_helmet", 0),
            "overloading": types_count.get("overloading", 0),
            "trend_labels": labels,
            "trend_data": trend,
            "type_labels": list(types_count.keys()),
            "type_data": list(types_count.values()),
            "finance_trend_paid": finance_trend_paid,
            "finance_trend_pending": finance_trend_pending,
            "finance_trend_weekly_paid": finance_trend_weekly_paid,
            "finance_trend_weekly_pending": finance_trend_weekly_pending,
            "finance_trend_weekly_labels": weekly_labels,
            "finance_trend_monthly_paid": finance_trend_monthly_paid,
            "finance_trend_monthly_pending": finance_trend_monthly_pending,
            "finance_trend_monthly_labels": monthly_labels,
            "revenue_labels": list(revenue_by_category.keys()),
            "revenue_data": list(revenue_by_category.values())
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
