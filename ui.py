from datetime import date
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from memory import MemoryStore, build_context_summary, is_onboarded, reset_profile


if TYPE_CHECKING:
    from agent import FitnessCoachAgent


console = Console()


def print_banner() -> None:
    console.print(
        Panel.fit(
            "[bold green]Coach Alex[/bold green]\n[green]Your personal weight loss coach[/green]",
            border_style="green",
            padding=(1, 4),
        )
    )


def print_coach(message: str) -> None:
    console.print("\n[bold green]Coach Alex:[/bold green]")
    console.print(Markdown(message))


def print_user(message: str) -> None:
    console.print(f"\n[bold blue]You:[/bold blue] {message}")


def print_status(message: str) -> None:
    console.print(message, style="dim")


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] [red]{message}[/red]")


def get_input() -> str:
    return Prompt.ask("[bold green]>[/bold green]", prompt_suffix=" ").strip()


def print_help() -> None:
    table = Table(title="Available Commands", border_style="green", header_style="bold green")
    table.add_column("Command", style="bold")
    table.add_column("What it does")
    table.add_row("quit", "Exit Coach Alex")
    table.add_row("reset", "Clear profile and chat history")
    table.add_row("status", "Show saved profile and recent logs")
    table.add_row("help", "Show this command table")
    console.print(table)


class FitnessCoachUI:
    def __init__(self, agent: "FitnessCoachAgent", memory: MemoryStore) -> None:
        self.agent = agent
        self.memory = memory

    def run(self) -> None:
        print_banner()
        print_help()

        if self._profile_is_empty() and Confirm.ask("Set up your profile now?", default=True):
            self.edit_profile()

        while True:
            user_message = get_input()
            if not user_message:
                continue

            command = user_message.lower()
            if command in {"quit", "exit"}:
                print_coach("See you next workout.")
                break
            if command == "help":
                print_help()
                continue
            if command == "profile":
                self.edit_profile()
                continue
            if command == "reset":
                reset_profile()
                print_status("Profile and chat history reset.")
                continue
            if command == "status":
                print_status(build_context_summary(self.memory.load_profile()))
                continue

            try:
                print_user(user_message)
                reply = self.agent.chat(user_message)
                print_coach(reply)
            except Exception as exc:
                print_error(str(exc))

    def edit_profile(self) -> None:
        profile = self.memory.load_profile()
        print_status("Profile setup")
        updates: dict[str, Any] = {
            "name": self._ask("Name", profile.get("name")),
            "age": self._ask_number("Age", profile.get("age")),
            "weight_kg": self._ask_number("Current weight in kg", profile.get("weight_kg")),
            "height_cm": self._ask_number("Height in cm", profile.get("height_cm")),
            "goal": self._ask("Goal", profile.get("goal")),
            "fitness_level": self._ask_choice(
                "Fitness level",
                ["beginner", "intermediate", "advanced"],
                profile.get("fitness_level"),
            ),
            "workout_days_per_week": self._ask_number(
                "Workout days per week",
                profile.get("workout_days_per_week"),
            ),
            "session_minutes": self._ask_number("Session length in minutes", profile.get("session_minutes")),
            "injuries": self._ask("Injuries or limitations", profile.get("injuries")),
            "food_preferences": self._ask("Food preferences", profile.get("food_preferences")),
            "allergies": self._ask("Allergies", profile.get("allergies")),
            "calorie_target": self._ask_number("Daily calorie target", profile.get("calorie_target")),
            "start_weight_kg": profile.get("start_weight_kg"),
            "joined_date": profile.get("joined_date") or date.today().isoformat(),
        }
        updates["start_weight_kg"] = updates["start_weight_kg"] or updates["weight_kg"]
        self.memory.save_profile(updates)
        print_status("Profile saved.")

    def _profile_is_empty(self) -> bool:
        profile = self.memory.load_profile()
        return not is_onboarded(profile)

    @staticmethod
    def _ask(label: str, current: Any) -> str:
        suffix = f" [{current}]" if current not in ("", None) else ""
        value = Prompt.ask(f"{label}{suffix}", default=str(current or ""))
        return value.strip()

    @staticmethod
    def _ask_number(label: str, current: Any) -> float | None:
        value = FitnessCoachUI._ask(label, current)
        if not value:
            return None
        try:
            return float(value)
        except ValueError:
            return current

    @staticmethod
    def _ask_choice(label: str, choices: list[str], current: Any) -> str:
        default = str(current) if current in choices else choices[0]
        return Prompt.ask(label, choices=choices, default=default)
