from dotenv import load_dotenv
import streamlit as st


WELCOME_MESSAGE = (
    "Hey! I'm Coach Alex, your personal fitness coach. I'm here to help you lose weight "
    "with home workouts and a meal plan that fits your life — no gym needed. What's your "
    "name, and what's your main goal right now?"
)


load_dotenv()

import agent
import memory
import tools


st.set_page_config(page_title="Coach Alex", page_icon="💪", layout="centered")


def load_state() -> None:
    if "user_data" not in st.session_state:
        st.session_state.user_data = memory.load_user_profile()
    if "history" not in st.session_state:
        st.session_state.history = memory.load_chat_history()
    if not st.session_state.history:
        st.session_state.history.append({"role": "assistant", "content": WELCOME_MESSAGE})
        memory.save_chat_history(st.session_state.history)


def save_state() -> None:
    memory.save_user_profile(st.session_state.user_data)
    memory.save_chat_history(st.session_state.history)


def status_messages(updates: dict) -> list[str]:
    messages = []
    if "weight_kg" in updates:
        messages.append("Weight logged ✓")
    if "workout_type" in updates:
        messages.append("Workout logged ✓")
    if "meal" in updates:
        messages.append("Meal logged ✓")
    if "calorie_target" in updates:
        messages.append(f"Calorie target set to {updates['calorie_target']} kcal ✓")
    return messages


load_state()

st.title("Coach Alex")
st.caption("Your personal weight loss coach")

with st.sidebar:
    st.header("Commands")
    if st.button("Status"):
        st.session_state.show_status = True
    if st.button("Reset"):
        memory.reset_profile()
        st.session_state.user_data = memory.load_user_profile()
        st.session_state.history = [{"role": "assistant", "content": WELCOME_MESSAGE}]
        save_state()
        st.rerun()
    st.markdown("Type `weekly check-in` in chat for a full weekly review.")

if st.session_state.get("show_status"):
    st.markdown(tools.format_weekly_summary(st.session_state.user_data))
    st.session_state.show_status = False

for message in st.session_state.history:
    avatar = "🏋️" if message["role"] == "assistant" else "🙂"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

user_message = st.chat_input("Message Coach Alex")
if user_message:
    command = user_message.strip().lower()

    if command == "help":
        st.info("Commands: status, reset, help, weekly check-in")
    elif command == "status":
        st.markdown(tools.format_weekly_summary(st.session_state.user_data))
    elif command == "reset":
        memory.reset_profile()
        st.session_state.user_data = memory.load_user_profile()
        st.session_state.history = [{"role": "assistant", "content": WELCOME_MESSAGE}]
        save_state()
        st.rerun()
    elif command in {"quit", "exit"}:
        save_state()
        st.info("Saved. You can close this browser tab.")
    else:
        with st.chat_message("user", avatar="🙂"):
            st.markdown(user_message)

        try:
            reply = agent.chat(st.session_state.history, user_message, st.session_state.user_data)
            updates = agent.extract_profile_updates(user_message, st.session_state.user_data)
            save_state()

            for status in status_messages(updates):
                st.toast(status)

            with st.chat_message("assistant", avatar="🏋️"):
                st.markdown(reply)
        except Exception as exc:
            st.error(f"Coach Alex hit an error: {exc}")
