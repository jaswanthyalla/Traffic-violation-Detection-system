"""
Database Module
Handles all database operations for traffic violation detection system
ONE BIKE → ONE VIOLATION PER DAY
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class DatabaseManager:
    """Centralized database management"""

    def __init__(self, db_path: str = "database/violations.db"):
        self.db_path = db_path
        self._ensure_database_exists()

    def _ensure_database_exists(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self._initialize_database()

    def _initialize_database(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    violation_type TEXT NOT NULL,
                    description TEXT,
                    location TEXT,
                    vehicle_info TEXT,
                    plate_number TEXT,
                    confidence REAL,
                    screenshot_path TEXT,
                    plate_screenshot_path TEXT,
                    fine_amount REAL,
                    status TEXT DEFAULT 'pending'
                )
            """)
            
            # Safe ALTER TABLE for existing DBs
            try:
                cursor.execute("ALTER TABLE violations ADD COLUMN plate_screenshot_path TEXT")
            except sqlite3.OperationalError:
                pass
                
            try:
                cursor.execute("ALTER TABLE violations ADD COLUMN fine_amount REAL")
            except sqlite3.OperationalError:
                pass

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT DEFAULT 'operator',
                    name TEXT,
                    last_login DATETIME
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS owners (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate_number TEXT UNIQUE,
                    owner_name TEXT,
                    phone TEXT
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS devices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    resolution TEXT DEFAULT '1080p',
                    status TEXT DEFAULT 'Online'
                )
            """)

            # Add dummy owner for testing if not exists
            cursor.execute("INSERT OR IGNORE INTO owners (plate_number, owner_name, phone) VALUES (?, ?, ?)", 
                           ("AP30ak5566", "Dummy Owner", "+919347637152"))

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_violations_timestamp 
                ON violations(timestamp)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_violations_status 
                ON violations(status)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_violations_type 
                ON violations(violation_type)
            """)

            # Create default admin user if no users exist
            cursor.execute("SELECT COUNT(*) FROM users")
            if cursor.fetchone()[0] == 0:
                from werkzeug.security import generate_password_hash
                admin_hash = generate_password_hash('admin123')
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, name)
                    VALUES (?, ?, ?, ?)
                """, ('admin', admin_hash, 'admin', 'Authority Admin'))

            conn.commit()
            conn.close()

            print(f"✅ Database initialized: {self.db_path}")

        except Exception as e:
            print(f"❌ Database init error: {e}")

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    # ==================================================
    # NEW FUNCTION — DAILY DUPLICATE CHECK
    # ==================================================
    def is_violation_already_today(self, plate_number: str, violation_type: str) -> bool:
        """
        Returns True if same bike already violated today
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            today = datetime.now().strftime("%Y-%m-%d")

            cursor.execute("""
                SELECT COUNT(*) FROM violations
                WHERE plate_number = ?
                AND violation_type = ?
                AND DATE(timestamp) = ?
            """, (plate_number, violation_type, today))

            count = cursor.fetchone()[0]
            conn.close()

            return count > 0

        except Exception as e:
            print("Daily check error:", e)
            return False

    # ==================================================
    # RECORD VIOLATION
    # ==================================================
    def record_violation(self, violation: Dict) -> int:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO violations 
                (violation_type, description, location, vehicle_info,
                 plate_number, confidence, screenshot_path, plate_screenshot_path, fine_amount, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                violation.get('type'),
                violation.get('description'),
                violation.get('location'),
                violation.get('vehicle_info'),
                violation.get('plate_number'),
                violation.get('confidence', 0),
                violation.get('screenshot_path'),
                violation.get('plate_screenshot_path'),
                violation.get('fine_amount', 0.0),
                'pending'
            ))

            conn.commit()
            violation_id = cursor.lastrowid
            conn.close()

            return violation_id

        except Exception as e:
            print("Error recording violation:", e)
            return -1

    # ==================================================
    # USER AUTHENTICATION
    # ==================================================
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            print("Get user error:", e)
            return None

    def create_user(self, username: str, password_hash: str, name: str, role: str = 'operator') -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (username, password_hash, name, role)
                VALUES (?, ?, ?, ?)
            """, (username, password_hash, name, role))
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # Username already exists
            print(f"User creation failed: username {username} already exists")
            return False
        except Exception as e:
            print("Create user error:", e)
            return False

    def update_password(self, user_id: int, new_password_hash: str) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Update password error:", e)
            return False

    def update_last_login(self, user_id: int):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print("Update last login error:", e)

    def get_all_users(self) -> List[Dict]:
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role, name, last_login FROM users ORDER BY name")
            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            print("Get all users error:", e)
            return []

    # ==================================================
    # REMAINING FUNCTIONS (UNCHANGED)
    # ==================================================
    
    def get_owner(self, plate_number: str):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT owner_name, phone FROM owners
                WHERE LOWER(plate_number) = LOWER(?)
            """, (plate_number,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "name": row[0],
                    "phone": row[1]
                }
            return None

        except Exception as e:
            print("Get owner error:", e)
            return None
    def get_recent_violations(self, limit: int = 50, hours: Optional[int] = None) -> List[Dict]:
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if hours:
                from datetime import timedelta
                since = (datetime.now() - timedelta(hours=hours)).isoformat()
                cursor.execute("""
                    SELECT * FROM violations
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (since, limit))
            else:
                cursor.execute("""
                    SELECT * FROM violations
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))

            data = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return data

        except Exception as e:
            print("Fetch error:", e)
            return []

    def get_violation_by_id(self, violation_id: int) -> Optional[Dict]:
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM violations WHERE id = ?", (violation_id,))
            row = cursor.fetchone()
            conn.close()

            return dict(row) if row else None
        except Exception as e:
            print("Fetch ID error:", e)
            return None

    def update_violation_status(self, violation_id: int, status: str) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE violations SET status = ? WHERE id = ?
            """, (status, violation_id))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print("Update error:", e)
            return False

    def search_by_plate(self, plate_number: str) -> List[Dict]:
        try:
            conn = self.get_connection()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM violations
                WHERE plate_number LIKE ?
                ORDER BY timestamp DESC
            """, (f"%{plate_number}%",))

            rows = [dict(r) for r in cursor.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            print("Search error:", e)
            return []

    # ==================================================
    # DEVICES
    # ==================================================
    def get_devices(self) -> List[Dict]:
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def add_device(self, name: str, ip_address: str, resolution: str = "1080p") -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO devices (name, ip_address, resolution, status) VALUES (?, ?, ?, 'Online')",
                (name, ip_address, resolution)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding device: {e}")
            return False

    def delete_device(self, device_id: int) -> bool:
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM devices WHERE id = ?", (device_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting device: {e}")
            return False

# ==================================================
# GLOBAL INSTANCE
# ==================================================
_db_instance = None


def get_database_manager(db_path: str = "database/violations.db") -> DatabaseManager:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance
