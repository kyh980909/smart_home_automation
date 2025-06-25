"""SQLite wrapper for storing device states and usage patterns."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Tuple


class SmartHomeDB:
    """Simple SQLite based persistence layer."""

    def __init__(self, db_file: str = "smarthome.db") -> None:
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self._create_tables()

    def _create_tables(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                type TEXT,
                status TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                device TEXT,
                action TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                condition TEXT,
                action TEXT,
                enabled INTEGER
            )
            """
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Pattern storage helpers
    def save_pattern(self, timestamp: datetime | str, device: str, action: str) -> None:
        """Insert a usage pattern entry."""

        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute(
            "INSERT INTO patterns (timestamp, device, action) VALUES (?, ?, ?)",
            (timestamp, device, action),
        )
        self.conn.commit()

    def get_patterns(self, start_date: datetime | str, end_date: datetime | str) -> List[Tuple]:
        """Return pattern rows between ``start_date`` and ``end_date``."""

        if isinstance(start_date, datetime):
            start_date = start_date.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(end_date, datetime):
            end_date = end_date.strftime("%Y-%m-%d %H:%M:%S")
        cur = self.conn.execute(
            "SELECT timestamp, device, action FROM patterns WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
            (start_date, end_date),
        )
        return cur.fetchall()

    # ------------------------------------------------------------------
    # Rule helpers
    def save_rule(self, condition: str, action: str) -> None:
        """Insert a new rule and enable it."""

        self.conn.execute(
            "INSERT INTO rules (condition, action, enabled) VALUES (?, ?, 1)",
            (condition, action),
        )
        self.conn.commit()

    def get_active_rules(self) -> List[Tuple]:
        """Return enabled rules."""

        cur = self.conn.execute(
            "SELECT id, condition, action FROM rules WHERE enabled = 1"
        )
        return cur.fetchall()

    # ------------------------------------------------------------------
    # Device helpers
    def update_device_status(self, device: str, status: str, type_: str | None = None) -> None:
        """Update status for ``device``; create the row if needed."""

        self.conn.execute(
            "INSERT OR IGNORE INTO devices (name, type, status) VALUES (?, ?, ?)",
            (device, type_ or "", status),
        )
        self.conn.execute(
            "UPDATE devices SET status = ? WHERE name = ?",
            (status, device),
        )
        self.conn.commit()

    def __del__(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
