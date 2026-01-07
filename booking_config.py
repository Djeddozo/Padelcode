import json
import os
from typing import Any, Dict, List

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "booking_schedule.json")
DEFAULT_SLOTS = [
    {"day": "Tuesday", "check_time": "19:59:00", "book_time": "20:00:00"},
    {"day": "Friday", "check_time": "19:59:00", "book_time": "20:00:00"},
]


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
        day = slot.get("day")
        check_time = slot.get("check_time")
        book_time = slot.get("book_time")
        if not isinstance(day, str) or not isinstance(check_time, str) or not isinstance(book_time, str):
            continue
        cleaned.append({"day": day, "check_time": check_time, "book_time": book_time})
    return cleaned or list(DEFAULT_SLOTS)


def save_schedule(slots: List[Dict[str, str]]) -> None:
    payload: Dict[str, Any] = {"slots": slots}
    with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
