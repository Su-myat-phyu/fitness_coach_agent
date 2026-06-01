# Coach Alex Fitness Coach Agent

A terminal-based personal weight loss coach for home workouts, meal planning, and daily accountability.

## Features

- Conversational onboarding for goals, schedule, fitness level, food preferences, allergies, and calorie target
- 7-day meal planner with calorie estimates and shopping list essentials
- Bodyweight home workout planner with warm-ups, circuits, HIIT, rest times, and cool-downs
- Natural-language logging for weight, meals, and workouts
- Weekly check-in with weight trend, workouts, average calories, wins, focus, and a fresh meal plan
- Persistent JSON memory for user profile and chat history
- Rich terminal UI with markdown table rendering

## Setup

### Step 1: Clone or download the project

Open a terminal in the project folder:

```bash
cd fitness_coach_agent
```

### Step 2: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Copy `.env.example` to `.env`

Windows:

```powershell
copy .env.example .env
```

macOS/Linux:

```bash
cp .env.example .env
```

### Step 4a: Groq backend

1. Sign up at `console.groq.com`.
2. Create a free API key.
3. Paste it into `.env`:

```env
BACKEND=groq
GROQ_API_KEY=your_groq_api_key_here
```

### Step 4b: Ollama backend

1. Install Ollama from `ollama.com`.
2. Pull the local model:

```bash
ollama pull llama3
```

3. Set `.env`:

```env
BACKEND=ollama
OLLAMA_MODEL=llama3
```

### Step 5: Run Coach Alex

```bash
python main.py
```

## Commands

| Command | Description |
| --- | --- |
| `quit` | Save and exit gracefully |
| `reset` | Clear profile and chat history |
| `status` | Show the current weekly summary |
| `help` | Show available commands |

## Logging Examples

Coach Alex understands natural language logs:

```text
I weigh 78kg
I had oats and banana for breakfast, about 420 calories
Just finished HIIT
I ate chicken salad for lunch 550 kcal
Completed a bodyweight circuit workout
```

## Project Structure

```text
fitness_coach_agent/
|-- main.py
|-- agent.py
|-- config.py
|-- memory.py
|-- prompts.py
|-- tools.py
|-- ui.py
|-- requirements.txt
|-- .env.example
|-- README.md
`-- data/
    |-- user_profile.json
    `-- chat_history.json
```

Coach Alex provides general fitness guidance only. For injuries, medical conditions, pregnancy, medication changes, eating disorders, or extreme weight-loss plans, talk with a qualified health professional.
