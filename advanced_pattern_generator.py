from __future__ import annotations

"""Advanced pattern generator limited to the existing five device types."""

from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any
import random


class AdvancedPatternGenerator:
    """Generate realistic weekday patterns using simple rule based logic."""

    def __init__(self) -> None:
        # Only use existing device types
        self.devices = [
            "거실조명",
            "주방조명",
            "침실1조명",
            "침실2조명",
            "침실3조명",
            "현관조명",
            "에어컨",
            "가스밸브",
            "보일러",
            "CCTV",
        ]

    # ------------------------------------------------------------------
    def generate_weekday_patterns(
        self, base_pattern: List[Dict[str, Any]], settings: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return 5 weekday pattern variations from ``base_pattern``."""

        season = settings.get("season", "spring")
        demographics = settings.get("demographics", {})
        complexity = float(settings.get("complexity", 0.5))
        start_date = settings.get("start_date", date.today())

        patterns: List[Dict[str, Any]] = []
        for i in range(5):
            day = start_date + timedelta(days=i)
            for ev in base_pattern:
                dt = datetime.combine(day, ev["time"])
                # basic random shift
                shift = random.randint(-30, 30)
                evt = {
                    "timestamp": dt + timedelta(minutes=shift),
                    "device": ev["device"],
                    "action": "power",
                    "value": ev["value"],
                }
                patterns.append(evt)

        patterns = self.apply_demographic_variations(patterns, demographics, complexity)
        patterns = self.apply_seasonal_variations(patterns, season)
        patterns.sort(key=lambda e: e["timestamp"])
        return patterns

    # ------------------------------------------------------------------
    def apply_demographic_variations(
        self, pattern: List[Dict[str, Any]], demographics: Dict[str, Any], complexity: float
    ) -> List[Dict[str, Any]]:
        """Apply age/gender based timing variations."""

        age = demographics.get("age", "adult").lower()

        result: List[Dict[str, Any]] = []
        for ev in pattern:
            new_ev = dict(ev)
            hour = ev["timestamp"].hour
            shift = random.randint(-15, 15)
            if age == "youth" and hour >= 20:
                shift += int(10 * complexity)
            elif age == "senior" and hour < 8:
                shift -= int(10 * complexity)
            new_ev["timestamp"] = ev["timestamp"] + timedelta(minutes=shift)
            result.append(new_ev)
        return result

    # ------------------------------------------------------------------
    def apply_seasonal_variations(
        self, pattern: List[Dict[str, Any]], season: str
    ) -> List[Dict[str, Any]]:
        """Modify pattern by season (aircon/boiler usage)."""

        season = season.lower()
        new_pattern: List[Dict[str, Any]] = []
        for ev in pattern:
            device = ev["device"]
            if device == "에어컨" and season == "winter":
                # skip aircon events in winter
                continue
            if device == "보일러" and season == "summer":
                # skip boiler events in summer
                continue
            new_pattern.append(ev)
        return new_pattern

    # ------------------------------------------------------------------
    def ai_generate_realistic_pattern(self, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return rule-based weekday patterns without a base input."""

        demographics = constraints.get("demographics", {})
        season = constraints.get("season", "spring")
        complexity = float(constraints.get("complexity", 0.5))

        base_schedule = [
            {"time": time(7, 0), "device": "현관조명", "value": "ON"},
            {"time": time(7, 5), "device": "주방조명", "value": "ON"},
            {"time": time(7, 10), "device": "가스밸브", "value": "ON"},
            {"time": time(8, 0), "device": "CCTV", "value": "ON"},
            {"time": time(18, 0), "device": "CCTV", "value": "OFF"},
            {"time": time(18, 5), "device": "거실조명", "value": "ON"},
            {"time": time(23, 0), "device": "거실조명", "value": "OFF"},
        ]
        return self.generate_weekday_patterns(
            base_schedule,
            {
                "season": season,
                "demographics": demographics,
                "complexity": complexity,
            },
        )

