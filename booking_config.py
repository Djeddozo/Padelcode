import json
import os
import re
from typing import Any, Dict, List

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "booking_schedule.json")
DEFAULT_SLOTS = [
    {"day": "Tuesday", "check_time": "19:00:00", "book_time": "20:00:00"},
    {"day": "Friday", "check_time": "19:00:00", "book_time": "20:00:00"},
]
HOUR_ONLY_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):00$")
HOUR_ONLY_WITH_SECONDS_PATTERN = re.compile(r"^(?:[01]\d|2[0-3]):00:00$")


def _normalize_hour_time(value: str) -> str | None:
    cleaned = value.strip()
    if HOUR_ONLY_WITH_SECONDS_PATTERN.match(cleaned):
        return cleaned
    if HOUR_ONLY_PATTERN.match(cleaned):
        return f"{cleaned}:00"
    return None


def _clean_slots(slots: List[Dict[str, str]]) -> List[Dict[str, str]]:
    cleaned_slots: List[Dict[str, str]] = []
    for slot in slots:
        day = slot.get("day")
        check_time = slot.get("check_time")
        book_time = slot.get("book_time")
        if not isinstance(day, str) or not isinstance(check_time, str) or not isinstance(book_time, str):
            continue
        normalized_check = _normalize_hour_time(check_time)
        normalized_book = _normalize_hour_time(book_time)
        if not normalized_check or not normalized_book:
            continue
        cleaned_slots.append({"day": day, "check_time": normalized_check, "book_time": normalized_book})
    return cleaned_slots


def load_schedule() -> List[Dict[str, str]]:
    if not os.path.exists(CONFIG_PATH):
        return list(DEFAULT_SLOTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return list(DEFAULT_SLOTS)
    slots = payload.get("slots")
    if not isinstance(slots, list):
        return list(DEFAULT_SLOTS)
    cleaned: List[Dict[str, str]] = []
    for slot in slots:
        if not isinstance(slot, dict):
            continue
        cleaned.append(slot)
    return _clean_slots(cleaned) or list(DEFAULT_SLOTS)


def save_schedule(slots: List[Dict[str, str]]) -> None:
    cleaned = _clean_slots(slots) or list(DEFAULT_SLOTS)
    payload: Dict[str, Any] = {"slots": cleaned}
    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
