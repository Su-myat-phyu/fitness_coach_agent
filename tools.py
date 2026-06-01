from datetime import date, datetime, timedelta
from typing import Any


ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
}


def calculate_tdee(
    weight_kg,
    height_cm,
    age,
    gender="unknown",
    activity="moderate",
) -> int:
    weight = float(weight_kg)
    height = float(height_cm)
    user_age = float(age)
    gender_key = str(gender).strip().lower()
    activity_key = str(activity).strip().lower()

    male_bmr = 10 * weight + 6.25 * height - 5 * user_age + 5
    female_bmr = 10 * weight + 6.25 * height - 5 * user_age - 161

    if gender_key in {"male", "man", "m"}:
        bmr = male_bmr
    elif gender_key in {"female", "woman", "f"}:
        bmr = female_bmr
    else:
        bmr = (male_bmr + female_bmr) / 2

    multiplier = ACTIVITY_MULTIPLIERS.get(activity_key, ACTIVITY_MULTIPLIERS["moderate"])
    return int(round(bmr * multiplier))


def suggest_calorie_target(tdee: int, goal="weight_loss") -> int:
    goal_key = str(goal).strip().lower().replace(" ", "_")
    if goal_key in {"weight_loss", "lose_weight", "fat_loss", "loss"}:
        return int(tdee - 500)
    if goal_key in {"muscle_gain", "gain_muscle", "bulk", "gain"}:
        return int(tdee + 300)
    return int(tdee)


def format_weekly_summary(user_data: dict) -> str:
    current_weight = _to_float(user_data.get("weight_kg"))
    start_weight = _to_float(user_data.get("start_weight_kg"))
    kg_lost = None
    if current_weight is not None and start_weight is not None:
        kg_lost = start_weight - current_weight

    workout_count = len(_entries_this_week(user_data.get("workout_log", [])))
    meal_entries = _entries_this_week(user_data.get("meal_log", []))
    avg_calories = _average_daily_calories(meal_entries)
    joined_date = _parse_date(user_data.get("joined_date"))
    days_since_joined = (date.today() - joined_date).days if joined_date else 0
    week_number = user_data.get("week_number") or 1

    weight_line = "Unknown"
    if current_weight is not None and start_weight is not None and kg_lost is not None:
        weight_line = f"{current_weight:.1f} kg vs {start_weight:.1f} kg start ({kg_lost:.1f} kg lost)"
    elif current_weight is not None:
        weight_line = f"{current_weight:.1f} kg"

    return "\n".join(
        [
            "## Weekly Summary",
            "",
            f"- **Current weight:** {weight_line}",
            f"- **Workouts completed this week:** {workout_count}",
            f"- **Average daily calories this week:** {avg_calories} kcal",
            f"- **Days since joined:** {days_since_joined}",
            f"- **Current week number:** {week_number}",
        ]
    )


def estimate_daily_calorie_target(profile: dict[str, Any]) -> str:
    try:
        tdee = calculate_tdee(
            profile.get("weight_kg"),
            profile.get("height_cm"),
            profile.get("age"),
            profile.get("gender", "unknown"),
            profile.get("activity", "moderate"),
        )
    except (TypeError, ValueError):
        return "Not enough profile data. Ask for age, height_cm, weight_kg, gender, and activity."

    target = suggest_calorie_target(tdee, profile.get("goal", "weight_loss"))
    return f"Estimated maintenance: {tdee} kcal/day. Suggested target: {target} kcal/day."


def _entries_this_week(entries: list) -> list:
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    return [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and (entry_date := _parse_date(entry.get("date"))) is not None
        and entry_date >= start_of_week
    ]


def _average_daily_calories(meal_entries: list) -> int:
    totals_by_date: dict[str, int] = {}
    for entry in meal_entries:
        entry_date = entry.get("date")
        kcal = _to_int(entry.get("kcal"))
        if entry_date and kcal is not None:
            totals_by_date[entry_date] = totals_by_date.get(entry_date, 0) + kcal

    if not totals_by_date:
        return 0
    return int(round(sum(totals_by_date.values()) / len(totals_by_date)))


def _parse_date(value: Any) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def _to_float(value: Any) -> float | None:
    try:
        if value in ("", None):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    try:
        if value in ("", None):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
