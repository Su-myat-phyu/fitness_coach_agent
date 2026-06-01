import re
from copy import deepcopy
from typing import Any

from groq import Groq

from config import BACKEND, GROQ_API_KEY, MAX_HISTORY_MESSAGES
from memory import (
    MemoryStore,
    is_onboarded,
    log_meal,
    log_weight,
    log_workout,
    save_chat_history,
    save_user_profile,
)
from prompts import build_system_prompt
from tools import calculate_tdee, format_weekly_summary, suggest_calorie_target


GROQ_MODEL = "llama3-70b-8192"


def chat(history: list, user_message: str, user_data: dict) -> str:
    _auto_calculate_calorie_target(user_data)
    prompt_data = _preview_user_data(user_message, user_data)

    system = build_system_prompt(prompt_data)
    if is_onboarded(prompt_data) and _needs_initial_plan(history):
        system = (
            f"{system}\n\nThe user has completed core onboarding. In this reply, generate a "
            "7-day meal plan markdown table and a bodyweight home workout plan."
        )
    if "weekly check-in" in user_message.lower():
        system = f"{system}\n\nComputed weekly summary:\n{format_weekly_summary(user_data)}"

    messages = history[-MAX_HISTORY_MESSAGES:] + [{"role": "user", "content": user_message}]

    if BACKEND != "groq":
        raise ValueError("Only the Groq backend is supported.")

    reply = _chat_with_groq(system, messages)

    reply = reply.strip()
    history.append({"role": "user", "content": user_message})
    history.append({"role": "assistant", "content": reply})
    del history[:-MAX_HISTORY_MESSAGES]
    return reply


def _chat_with_groq(system: str, messages: list) -> str:
    client = Groq(api_key=GROQ_API_KEY)
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            system=system,
            messages=messages,
            temperature=0.7,
            max_tokens=900,
        )
    except TypeError:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": system}, *messages],
            temperature=0.7,
            max_tokens=900,
        )
    return response.choices[0].message.content


def extract_profile_updates(user_message: str, user_data: dict) -> dict:
    updates: dict[str, Any] = {}
    text = user_message.strip()

    updates.update(_extract_onboarding_fields(text, user_data))

    weight_match = re.search(
        r"\b(?:i\s+weigh|weighing|weight\s+is|current\s+weight\s+is)\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms)\b",
        text,
        flags=re.IGNORECASE,
    )
    if weight_match:
        weight_kg = float(weight_match.group(1))
        log_weight(user_data, weight_kg)
        updates["weight_kg"] = weight_kg

    workout_match = re.search(
        r"\b(?:just\s+finished|finished|completed|did|done\s+with)\s+(?:a\s+|an\s+|my\s+)?([a-z0-9\s-]*(?:hiit|circuit|workout|training|cardio|strength|yoga|pilates|walk|run)[a-z0-9\s-]*)",
        text,
        flags=re.IGNORECASE,
    )
    if workout_match:
        workout_type = workout_match.group(1).strip(" .,!").lower()
        log_workout(user_data, workout_type)
        updates["workout_type"] = workout_type

    meal_match = re.search(
        r"\b(?:i\s+had|i\s+ate|i\s+drank|my\s+(?:breakfast|lunch|dinner|snack)\s+was)\s+(.+?)(?:\s+(?:for|at)\s+(?:breakfast|lunch|dinner|snack))?(?:[.!?]|$)",
        text,
        flags=re.IGNORECASE,
    )
    if meal_match:
        meal = meal_match.group(1).strip(" .,!").lower()
        kcal_match = re.search(r"\b(\d{2,4})\s*(?:kcal|calories|cals|cal)\b", text, flags=re.IGNORECASE)
        kcal = int(kcal_match.group(1)) if kcal_match else 0
        log_meal(user_data, meal, kcal)
        updates["meal"] = meal
        updates["kcal"] = kcal

    for key, value in updates.items():
        if key not in {"weight_kg", "workout_type", "meal", "kcal"}:
            user_data[key] = value

    calorie_target = _auto_calculate_calorie_target(user_data)
    if calorie_target is not None:
        updates["calorie_target"] = calorie_target
    return updates


def _preview_user_data(user_message: str, user_data: dict) -> dict:
    preview = deepcopy(user_data)
    preview.update(_extract_onboarding_fields(user_message, preview))

    weight_match = re.search(
        r"\b(?:i\s+weigh|weighing|weight\s+is|current\s+weight\s+is)\s*(\d+(?:\.\d+)?)\s*(?:kg|kgs|kilograms)\b",
        user_message,
        flags=re.IGNORECASE,
    )
    if weight_match:
        preview["weight_kg"] = float(weight_match.group(1))
        preview["start_weight_kg"] = preview.get("start_weight_kg") or preview["weight_kg"]

    if preview.get("calorie_target") in ("", None) and all(
        preview.get(field) not in ("", None) for field in ("weight_kg", "height_cm", "age")
    ):
        try:
            tdee = calculate_tdee(
                preview["weight_kg"],
                preview["height_cm"],
                preview["age"],
                preview.get("gender", "unknown"),
                preview.get("activity", "moderate"),
            )
            preview["calorie_target"] = suggest_calorie_target(tdee, preview.get("goal", "weight_loss"))
        except (TypeError, ValueError):
            pass

    return preview


def _extract_onboarding_fields(text: str, user_data: dict) -> dict:
    updates: dict[str, Any] = {}

    name_match = re.search(r"\b(?:my name is|call me)\s+([A-Z][a-zA-Z'-]+)\b", text, flags=re.IGNORECASE)
    if name_match and not user_data.get("name"):
        updates["name"] = name_match.group(1).strip().title()

    age_match = re.search(r"\b(?:i am|i'm|age is)\s+(\d{1,2})\s*(?:years old|yo)?\b", text, flags=re.IGNORECASE)
    if age_match:
        updates["age"] = int(age_match.group(1))

    height_match = re.search(
        r"\b(?:i am|i'm|height is)\s*(\d{2,3}(?:\.\d+)?)\s*(?:cm|centimeters)\b",
        text,
        flags=re.IGNORECASE,
    )
    if height_match:
        updates["height_cm"] = float(height_match.group(1))

    goal_match = re.search(
        r"\b(?:my goal is|goal is|i want to|i'd like to)\s+(.+?)(?:[.!?]|$)",
        text,
        flags=re.IGNORECASE,
    )
    if goal_match:
        updates["goal"] = goal_match.group(1).strip(" .,!")

    food_match = re.search(
        r"\b(?:food preferences are|i prefer|i like eating|diet is)\s+(.+?)(?:[.!?]|$)",
        text,
        flags=re.IGNORECASE,
    )
    if food_match:
        updates["food_preferences"] = food_match.group(1).strip(" .,!")

    allergies_match = re.search(
        r"\b(?:allergies are|i am allergic to|i'm allergic to)\s+(.+?)(?:[.!?]|$)",
        text,
        flags=re.IGNORECASE,
    )
    if allergies_match:
        updates["allergies"] = allergies_match.group(1).strip(" .,!")

    fitness_match = re.search(r"\b(beginner|intermediate|advanced)\b", text, flags=re.IGNORECASE)
    if fitness_match:
        updates["fitness_level"] = fitness_match.group(1).lower()

    days_match = re.search(
        r"\b(\d)\s*(?:days|x)\s*(?:a|per)?\s*week\b",
        text,
        flags=re.IGNORECASE,
    )
    if days_match:
        updates["workout_days_per_week"] = int(days_match.group(1))

    session_match = re.search(
        r"\b(\d{2,3})\s*(?:minute|minutes|min)\b",
        text,
        flags=re.IGNORECASE,
    )
    if session_match:
        updates["session_minutes"] = int(session_match.group(1))

    calorie_match = re.search(
        r"\b(?:calorie target is|target is|aiming for)\s*(\d{3,4})\s*(?:kcal|calories|cals)?\b",
        text,
        flags=re.IGNORECASE,
    )
    if calorie_match:
        updates["calorie_target"] = int(calorie_match.group(1))

    return updates


def _auto_calculate_calorie_target(user_data: dict) -> int | None:
    if user_data.get("calorie_target") not in ("", None):
        return None

    required_fields = ("weight_kg", "height_cm", "age")
    if any(user_data.get(field) in ("", None) for field in required_fields):
        return None

    try:
        tdee = calculate_tdee(
            user_data["weight_kg"],
            user_data["height_cm"],
            user_data["age"],
            user_data.get("gender", "unknown"),
            user_data.get("activity", "moderate"),
        )
    except (TypeError, ValueError):
        return None

    user_data["calorie_target"] = suggest_calorie_target(tdee, user_data.get("goal", "weight_loss"))
    save_user_profile(user_data)
    return user_data["calorie_target"]


def _needs_initial_plan(history: list) -> bool:
    combined = "\n".join(str(message.get("content", "")).lower() for message in history)
    return "shopping list essentials" not in combined and "warm-up" not in combined


class FitnessCoachAgent:
    def __init__(self, memory: MemoryStore) -> None:
        self.memory = memory

    def chat(self, user_message: str) -> str:
        profile = self.memory.load_profile()
        history = self.memory.load_history()
        reply = chat(history, user_message, profile)
        save_chat_history(history)
        return reply
