"""Utilities for generating and analyzing simple device usage patterns."""

from __future__ import annotations

import csv
import random
from datetime import datetime, date, time, timedelta
from typing import Iterable, List, Dict, Any

__all__ = [
    "generate_daily_pattern",
    "add_variation",
    "save_to_csv",
    "load_from_csv",
    "analyze_pattern",
]


Event = Dict[str, Any]


def _ensure_date(day: date | str) -> date:
    """Return ``day`` as :class:`~datetime.date`."""

    if isinstance(day, date):
        return day
    return datetime.strptime(str(day), "%Y-%m-%d").date()


def generate_daily_pattern(day: date | str) -> List[Event]:
    """Return a list of events for a typical day.

    The pattern is as follows (24h time):

    - ``07:00`` ``거실조명`` ON
    - ``08:00`` 모든 조명 OFF, 보일러 외출모드
    - ``18:00`` ``거실조명`` ON, 보일러 재실모드
    - ``23:00`` 모든 조명 OFF
    """

    base_date = _ensure_date(day)

    def dt(h: int, m: int) -> datetime:
        return datetime.combine(base_date, time(h, m))

    pattern: List[Event] = [
        {"timestamp": dt(7, 0), "device": "거실조명", "action": "power", "value": "ON"},
        {"timestamp": dt(8, 0), "device": "모든조명", "action": "power", "value": "OFF"},
        {"timestamp": dt(8, 0), "device": "보일러", "action": "mode", "value": "외출"},
        {"timestamp": dt(18, 0), "device": "거실조명", "action": "power", "value": "ON"},
        {"timestamp": dt(18, 0), "device": "보일러", "action": "mode", "value": "재실"},
        {"timestamp": dt(23, 0), "device": "모든조명", "action": "power", "value": "OFF"},
    ]
    return pattern


def add_variation(pattern: Iterable[Event], variation_level: float = 1.0) -> List[Event]:
    """Return ``pattern`` with random time shifts and occasional drops.

    ``variation_level`` is a float from ``0`` to ``1`` controlling the
    intensity of the variation.
    """

    new_pattern: List[Event] = []
    for event in pattern:
        if random.random() < 0.1 * variation_level:
            # skip event
            continue
        shift = int(random.uniform(-30, 30) * variation_level)
        new_time = event["timestamp"] + timedelta(minutes=shift)
        new_event = dict(event)
        new_event["timestamp"] = new_time
        new_pattern.append(new_event)

    new_pattern.sort(key=lambda e: e["timestamp"])
    return new_pattern


def save_to_csv(patterns: Iterable[Event], filename: str) -> None:
    """Write ``patterns`` to ``filename`` as CSV."""

    with open(filename, "w", newline="") as fp:
        writer = csv.DictWriter(
            fp, fieldnames=["timestamp", "device", "action", "value"]
        )
        writer.writeheader()
        for event in patterns:
            row = dict(event)
            if isinstance(row["timestamp"], datetime):
                row["timestamp"] = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(row)


def load_from_csv(filename: str) -> List[Event]:
    """Read pattern events from ``filename``."""

    events: List[Event] = []
    with open(filename, newline="") as fp:
        reader = csv.DictReader(fp)
        for row in reader:
            row["timestamp"] = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")
            events.append(row)
    return events


def analyze_pattern(patterns: Iterable[Event]) -> Dict[str, Dict[str, int]]:
    """Return repeated device/time pairs appearing at least 3 times."""

    counts: Dict[str, Dict[str, int]] = {}
    for event in patterns:
        device = event["device"]
        time_key = event["timestamp"].strftime("%H:%M")
        counts.setdefault(device, {})[time_key] = counts.get(device, {}).get(time_key, 0) + 1

    repeated: Dict[str, Dict[str, int]] = {}
    for device, time_map in counts.items():
        frequent = {t: c for t, c in time_map.items() if c >= 3}
        if frequent:
            repeated[device] = frequent
    return repeated

