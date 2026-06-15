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
                    status TEXT DEFAULT 'pending'
                )
            """)

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
                 plate_number, confidence, screenshot_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                violation.get('type'),
                violation.get('description'),
                violation.get('location'),
                violation.get('vehicle_info'),
                violation.get('plate_number'),
                violation.get('confidence', 0),
                violation.get('screenshot_path'),
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
# GLOBAL INSTANCE
# ==================================================
_db_instance = None


def get_database_manager(db_path: str = "database/violations.db") -> DatabaseManager:
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager(db_path)
    return _db_instance
