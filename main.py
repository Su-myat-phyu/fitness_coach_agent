from dotenv import load_dotenv
from rich.prompt import Confirm


WELCOME_MESSAGE = (
    "Hey! I'm Coach Alex, your personal fitness coach. I'm here to help you lose weight "
    "with home workouts and a meal plan that fits your life \u2014 no gym needed. What's your "
    "name, and what's your main goal right now?"
)


def main() -> None:
    load_dotenv()

    import agent
    import memory
    import tools
    import ui

    user_data = memory.load_user_profile()
    history = memory.load_chat_history()

    try:
        ui.print_banner()
        ui.print_help()

        if not history:
            ui.print_coach(WELCOME_MESSAGE)
            history.append({"role": "assistant", "content": WELCOME_MESSAGE})
            memory.save_chat_history(history)

        while True:
            try:
                user_message = ui.get_input()
            except (KeyboardInterrupt, EOFError):
                _save_and_exit(memory, history, user_data, ui)
                return

            if not user_message:
                continue

            command = user_message.lower().strip()

            if command in {"quit", "exit"}:
                _save_and_exit(memory, history, user_data, ui)
                return

            if command == "reset":
                if Confirm.ask("Reset profile and chat history?", default=False):
                    memory.reset_profile()
                    user_data = memory.load_user_profile()
                    history = memory.load_chat_history()
                    ui.print_status("Profile and chat history reset. Starting fresh.")
                    ui.print_coach(WELCOME_MESSAGE)
                    history.append({"role": "assistant", "content": WELCOME_MESSAGE})
                    memory.save_chat_history(history)
                continue

            if command == "status":
                ui.print_coach(tools.format_weekly_summary(user_data))
                continue

            if command == "help":
                ui.print_help()
                continue

            ui.print_user(user_message)

            try:
                reply = agent.chat(history, user_message, user_data)
            except Exception as exc:
                if _is_api_error(exc):
                    ui.print_error(f"LLM API error: {exc}")
                    continue
                ui.print_error(f"Unexpected error: {exc}")
                continue

            updates = agent.extract_profile_updates(user_message, user_data)
            _print_update_statuses(updates, ui)
            ui.print_coach(reply)
            memory.save_chat_history(history)
            memory.save_user_profile(user_data)

    except (KeyboardInterrupt, EOFError):
        _save_and_exit(memory, history, user_data, ui)
    except Exception as exc:
        ui.print_error(f"Unexpected error: {exc}")
        memory.save_chat_history(history)
        memory.save_user_profile(user_data)


def _save_and_exit(memory_module, history: list, user_data: dict, ui_module) -> None:
    memory_module.save_chat_history(history)
    memory_module.save_user_profile(user_data)
    ui_module.print_status("Saved. See you next workout.")


def _print_update_statuses(updates: dict, ui_module) -> None:
    if "weight_kg" in updates:
        ui_module.print_status("Weight logged \u2713")
    if "workout_type" in updates:
        ui_module.print_status("Workout logged \u2713")
    if "meal" in updates:
        ui_module.print_status("Meal logged \u2713")
    if "calorie_target" in updates:
        ui_module.print_status(f"Calorie target set to {updates['calorie_target']} kcal \u2713")


def _is_api_error(exc: Exception) -> bool:
    module_name = exc.__class__.__module__.lower()
    class_name = exc.__class__.__name__.lower()
    api_markers = (
        "api",
        "authentication",
        "permission",
        "rate",
        "response",
        "request",
        "timeout",
        "connection",
    )
    return "groq" in module_name or "ollama" in module_name or any(marker in class_name for marker in api_markers)


if __name__ == "__main__":
    main()
