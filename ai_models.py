# AI models for pattern analysis

from __future__ import annotations

from typing import List, Tuple

import pandas as pd


class PatternAnalyzer:
    """Very small helper class for analysing device usage patterns."""

    def __init__(self) -> None:
        self.patterns: list[Tuple[str, str, str, int]] = []

    # ------------------------------------------------------------------
    def find_repeated_patterns(self, data: pd.DataFrame) -> List[Tuple[str, str, str, int]]:
        """Return repeated ``device/time/action`` combinations.

        ``data`` is expected to contain ``timestamp``, ``device`` and ``value``
        columns.  ``timestamp`` should be parseable by ``pandas``.  A pattern
        is considered repeated when the same combination occurs three or more
        times.
        """

        if data.empty:
            self.patterns = []
            return self.patterns

        df = data.copy()
        df["time"] = pd.to_datetime(df["timestamp"]).dt.strftime("%H:%M")

        grouped = (
            df.groupby(["device", "time", "value"])
            .size()
            .reset_index(name="count")
        )

        results: list[Tuple[str, str, str, int]] = []
        for _, row in grouped.iterrows():
            if row["count"] >= 3:
                results.append(
                    (str(row["device"]), str(row["time"]), str(row["value"]), int(row["count"]))
                )

        self.patterns = results
        return results

    # ------------------------------------------------------------------
    def detect_anomaly(self, current_action: dict, historical_data: pd.DataFrame) -> bool:
        """Return ``True`` if ``current_action`` is far from the historical mean.

        ``current_action`` should have a ``timestamp`` key. ``historical_data``
        contains past entries for the same device and action.  If the time of
        ``current_action`` differs from the average historical time by two hours
        or more, the action is flagged as anomalous.
        """

        if historical_data.empty:
            return False

        times = pd.to_datetime(historical_data["timestamp"])
        minutes = times.dt.hour * 60 + times.dt.minute
        mean_min = minutes.mean()

        cur_time = pd.to_datetime(current_action["timestamp"])
        cur_min = cur_time.hour * 60 + cur_time.minute

        return abs(cur_min - mean_min) >= 120

    # ------------------------------------------------------------------
    def generate_rules(self, patterns: List[Tuple[str, str, str, int]]) -> List[str]:
        """Convert pattern tuples to simple if-then rule strings."""

        rules: list[str] = []
        for device, time, action, _ in patterns:
            if action.upper() == "ON":
                cmd = f"turn_on('{device}')"
            elif action.upper() == "OFF":
                cmd = f"turn_off('{device}')"
            else:
                cmd = f"set_state('{device}', '{action}')"
            rules.append(f"if time == '{time}' then {cmd}")

        return rules

