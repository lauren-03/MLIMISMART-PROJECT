# -*- coding: utf-8 -*-
"""Turns the advice model's decision into the advice the farmer receives."""
from dataclasses import dataclass, field
from datetime import date

from ..data.knowledge_base import knowledge_for, msg
from ..ml.actions import ACTIONS, expert_label, wording

# Weather alert thresholds (used by weather_service.alerts).
HEAVY_RAIN_PROBABILITY = 70
HEAVY_RAIN_MM = 15.0
HOT_TEMPERATURE = 30.0
HIGH_HUMIDITY = 85
STRONG_WIND_KPH = 35.0


@dataclass
class Advice:
    topic: str
    urgency: str = "normal"
    action: str | None = None
    points_en: list[str] = field(default_factory=list)
    points_ny: list[str] = field(default_factory=list)
    rules_fired: list[str] = field(default_factory=list)
    confidence: float = 1.0
    method: str = "model"
    situational_count: int = 0

    def body(self, language: str, *, brief: bool = False) -> str:
        points = self.points_ny if language == "NY" else self.points_en
        if brief and self.situational_count:
            points = points[: self.situational_count]
        return " ".join(points)

    def reasoning(self) -> str:
        return " | ".join(self.rules_fired)


def current_season(today: date | None = None) -> str:
    month = (today or date.today()).month
    if month in (11, 12, 1, 2, 3, 4):
        return "rainy"
    if month in (5, 6, 7, 8):
        return "cool_dry"
    return "hot_dry"


def season_label(season: str, language: str) -> str:
    labels = {
        "rainy": ("the rainy season", "nyengo ya mvula"),
        "cool_dry": ("the cool dry season", "nyengo yozizira youma"),
        "hot_dry": ("the hot dry season", "nyengo yotentha youma"),
    }
    en, ny = labels[season]
    return ny if language == "NY" else en


def generate(topic: str, situation: dict, decision: dict | None, rain: dict | None, *,
             confidence: float = 1.0, method: str = "model") -> Advice:
    advice = Advice(topic=topic, confidence=confidence, method=method)

    if topic not in ACTIONS:
        advice.rules_fired.append("topic not recognised: showing what MlimiSmart can advise on")
        advice.points_en = [msg("no_topic", "EN")]
        advice.points_ny = [msg("no_topic", "NY")]
        return advice

    if decision:
        action = decision["action"]
        others = ", ".join(f"{a} {p:.0%}" for a, p in sorted(
            decision["scores"].items(), key=lambda kv: -kv[1]) if a != action)
        advice.rules_fired.append(
            f"advice model v{decision['version']} chose {action} ({decision['confidence']:.0%})")
        if others:
            advice.rules_fired.append(f"other options: {others}")
    else:
        action = expert_label(topic, situation)
        advice.rules_fired.append(f"advice model not trained yet: tea guidance gives {action}")

    if rain:
        advice.rules_fired.append(
            f"rain model v{rain['model_version']}: {rain['probability']:.0%} chance of rain on {rain['target_day']}")
    advice.rules_fired.append(
        f"inputs: rain today {situation['rain_today']:.1f} mm, tomorrow {situation['rain_tomorrow']:.1f} mm, "
        f"last 3 days {situation['rain_3d']:.1f} mm, max {situation['tmax']:.0f}C, "
        f"humidity {situation['humidity']:.0f}%, month {situation['month']}")
    soil, anomaly = situation.get("soil_moisture"), situation.get("rain_anomaly")
    if soil is not None:
        advice.rules_fired.append(f"soil moisture (ERA5-Land): {soil:.2f} m3/m3")
    if anomaly is not None:
        word = "above" if anomaly >= 0 else "below"
        advice.rules_fired.append(f"CHIRPS: rainfall two months ago was {abs(anomaly):.0f} mm {word} normal")

    advice.action = action
    advice.urgency, text_en = wording(topic, action, "EN")
    _, text_ny = wording(topic, action, "NY")
    advice.points_en.append(text_en)
    advice.points_ny.append(text_ny)
    advice.situational_count = 1
    advice.points_en.append(knowledge_for(topic, "EN"))
    advice.points_ny.append(knowledge_for(topic, "NY"))
    return advice
