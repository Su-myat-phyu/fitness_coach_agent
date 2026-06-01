import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from typing import Any

from config import MAX_HISTORY_MESSAGES


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
PROFILE_PATH = DATA_DIR / "user_profile.json"
HISTORY_PATH = DATA_DIR / "chat_history.json"


DEFAULT_USER_PROFILE: dict[str, Any] = {
    "name": "",
    "age": None,
    "weight_kg": None,
    "height_cm": None,
    "goal": "",
    "fitness_level": "",
    "workout_days_per_week": None,
    "session_minutes": None,
    "injuries": "",
    "food_preferences": "",
    "allergies": "",
    "calorie_target": None,
    "start_weight_kg": None,
    "weight_log": [],
    "workout_log": [],
    "meal_log": [],
    "week_number": 1,
    "joined_date": "",
}


def load_user_profile() -> dict:
    data = _read_json(PROFILE_PATH, {})
    if not isinstance(data, dict):
        data = {}

    profile = deepcopy(DEFAULT_USER_PROFILE)
    profile.update(data)
    return profile


def save_user_profile(data: dict) -> None:
    profile = deepcopy(DEFAULT_USER_PROFILE)
    profile.update(data)
    _write_json(PROFILE_PATH, profile)


def load_chat_history() -> list:
    history = _read_json(HISTORY_PATH, [])
    return history if isinstance(history, list) else []


def save_chat_history(history: list) -> None:
    _write_json(HISTORY_PATH, history[-MAX_HISTORY_MESSAGES:])


def is_onboarded(data: dict) -> bool:
    required_fields = ("name", "weight_kg", "goal", "food_preferences")
    return all(data.get(field) not in ("", None, []) for field in required_fields)


def log_weight(data: dict, weight_kg: float) -> None:
    data.setdefault("weight_log", [])
    data["weight_log"].append({"date": _today(), "weight_kg": weight_kg})
    data["weight_kg"] = weight_kg
    if data.get("start_weight_kg") in ("", None):
        data["start_weight_kg"] = weight_kg
    save_user_profile(data)


def log_workout(data: dict, workout_type: str) -> None:
    data.setdefault("workout_log", [])
    data["workout_log"].append({"date": _today(), "workout_type": workout_type})
    save_user_profile(data)


def log_meal(data: dict, meal: str, kcal: int) -> None:
    data.setdefault("meal_log", [])
    data["meal_log"].append({"date": _today(), "meal": meal, "kcal": kcal})
    save_user_profile(data)


def build_context_summary(data: dict) -> str:
    profile = deepcopy(DEFAULT_USER_PROFILE)
    profile.update(data)

    profile_lines = [
        f"Name: {profile['name'] or 'Unknown'}",
        f"Age: {_format_value(profile['age'])}",
        f"Weight kg: {_format_value(profile['weight_kg'])}",
        f"Height cm: {_format_value(profile['height_cm'])}",
        f"Goal: {profile['goal'] or 'Unknown'}",
        f"Fitness level: {profile['fitness_level'] or 'Unknown'}",
        f"Workout days per week: {_format_value(profile['workout_days_per_week'])}",
        f"Session minutes: {_format_value(profile['session_minutes'])}",
        f"Injuries: {profile['injuries'] or 'None listed'}",
        f"Food preferences: {profile['food_preferences'] or 'Unknown'}",
        f"Allergies: {profile['allergies'] or 'None listed'}",
        f"Calorie target: {_format_value(profile['calorie_target'])}",
        f"Start weight kg: {_format_value(profile['start_weight_kg'])}",
        f"Week number: {_format_value(profile['week_number'])}",
        f"Joined date: {profile['joined_date'] or 'Unknown'}",
    ]

    return "\n".join(
        [
            "User profile:",
            *profile_lines,
            "",
            "Recent weight logs:",
            *_format_recent_logs(profile["weight_log"]),
            "",
            "Recent workout logs:",
            *_format_recent_logs(profile["workout_log"]),
            "",
            "Recent meal logs:",
            *_format_recent_logs(profile["meal_log"]),
        ]
    )


def reset_profile() -> None:
    _write_json(PROFILE_PATH, deepcopy(DEFAULT_USER_PROFILE))
    _write_json(HISTORY_PATH, [])


class MemoryStore:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _ensure_json(PROFILE_PATH, deepcopy(DEFAULT_USER_PROFILE))
        _ensure_json(HISTORY_PATH, [])

    def load_profile(self) -> dict[str, Any]:
        return load_user_profile()

    def save_profile(self, profile: dict[str, Any]) -> None:
        save_user_profile(profile)

    def update_profile(self, updates: dict[str, Any]) -> dict[str, Any]:
        profile = load_user_profile()
        profile.update(updates)
        save_user_profile(profile)
        return profile

    def load_history(self) -> list[dict[str, str]]:
        return load_chat_history()

    def append_message(self, role: str, content: str) -> None:
        history = load_chat_history()
        history.append({"role": role, "content": content})
        save_chat_history(history)

    def clear_history(self) -> None:
        save_chat_history([])


def _ensure_json(path: Path, default: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        _write_json(path, default)


def _read_json(path: Path, default: Any) -> Any:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, FileNotFoundError):
        return deepcopy(default)


def _write_json(path: Path, data: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)
        file.write("\n")


def _today() -> str:
    return date.today().isoformat()


def _format_value(value: Any) -> str:
    return "Unknown" if value in ("", None, []) else str(value)


def _format_recent_logs(logs: list) -> list[str]:
    if not logs:
        return ["- None yet"]
    return [f"- {entry}" for entry in logs[-7:]]
