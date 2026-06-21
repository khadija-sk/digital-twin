# Digital Twin

> Your digital self — tracking and growing with you.

An AI-powered personal productivity desktop application that combines habit tracking, journaling, goal management, and academic tools with a multi-LLM conversational assistant that genuinely remembers who you are.

Built with **PySide6**, **SQLAlchemy**, and a multi-provider LLM architecture (Gemini, Grok, Claude, Ollama).

---

## ✨ Why this project

Most AI assistants forget everything the moment a session ends. Digital Twin was built around a different idea: what if your daily habits, goals, journal entries, and academic progress fed into a single persistent memory — so every conversation builds on the last?

## 🧠 Core features

### AI & Memory
- **Persistent memory system** — entries stored with embeddings, retrieved via cosine similarity
- **ContextRetriever** — aggregates profile, daily logs, study sessions, journal entries, goals, and memories into a single unified context
- **Shared prompt builder** — every LLM provider receives the exact same rich system prompt, no duplicated logic
- **Multi-LLM architecture** — Gemini and Grok as primary providers (hash-balanced), with Claude and Ollama as cascading fallbacks
- **Question router** — routes queries by type (general, complex, code, creative, data)
- **Real-time web search** integrated directly into the chat (DuckDuckGo, no API key required)
- **Voice support** — Text-to-Speech and Speech-to-Text

### Productivity
- Daily check-ins (mood, energy, sleep) with streak tracking
- Pomodoro timer with session history
- Goal management with AI-generated subtasks, progress tracking, and inactivity detection
- AI-analyzed journal — extracts mood, motivation, stress, and recurring themes
- Unified calendar combining assignments, goals, timeline events, and study sessions
- Academic assistant — course/assignment tracking, exam prep readiness

### Insights & Engagement
- **Daily briefing** — proactive summary of streak, mood, productivity, and upcoming deadlines
- **Predictive analytics** — next-day productivity score and trend direction
- **Personalized recommendations** and a daily challenge tailored to behavior
- **Gamification** — XP, levels, streaks, and unlockable badges
- Radar-chart analytics (productivity, mood, energy, sleep, consistency, sessions)
- Exportable reports (PDF, DOCX, CSV, TXT)

### Interface
- 15+ pages with a clean sidebar navigation
- Light / dark theme support
- Toast notifications, animated badge unlocks, loading states throughout

---

## 🏗️ Architecture

```
┌─────────────────────┐         ┌─────────────────────┐
│  Interface (PySide6)│         │   AI Panel (Chat)    │
└──────────┬───────────┘         └──────────┬──────────┘
           │                                 │
           └───────────────┬─────────────────┘
                            ▼
              ┌─────────────────────────┐
              │   Application Layer      │
              │  Controllers & Services  │
              └─────────────┬─────────────┘
                            ▼
        ┌───────────┬───────────────┬───────────────┐
        │  Service  │   AI Engine    │  Data Access  │
        │   Layer   │ (ContextRetriever,│    Layer    │
        │           │ PromptBuilder,    │  (SQLAlchemy)│
        │           │ ProviderFactory)  │              │
        └───────────┴───────────────┴───────────────┘
                            ▼
        ┌─────────┬─────────┬─────────┬─────────┐
        │ Gemini  │  Grok   │ Claude  │ Ollama  │
        └─────────┴─────────┴─────────┴─────────┘
                            ▼
                  ┌──────────────────┐
                  │  SQLite Database  │
                  └──────────────────┘
```

A full architecture diagram is available in [`/docs/architecture.png`](./docs/architecture.png).

---

## 🛠️ Tech stack

| Layer | Technology |
|---|---|
| UI | PySide6 (Qt6) |
| ORM / Database | SQLAlchemy + SQLite |
| Auth | bcrypt |
| LLM providers | google-genai (Gemini), anthropic (Claude), requests (Grok, Ollama) |
| Embeddings / similarity | numpy |
| Exports | fpdf2 (PDF), python-docx (DOCX) |
| Notifications | plyer |
| Sound | pygame |
| Voice | speech_recognition, sounddevice, QtTextToSpeech |

---

## 📂 Project structure

```
digital_twin/
├── main.py                 # Entry point, routing, bootstrap
├── models/                 # SQLAlchemy ORM models
├── controllers/             # Business logic (Auth, AI, Goals, Journal, Timer, LLM...)
├── services/                # Memory, analytics, planning, prompt building, LLM providers
│   └── llm/                 # Provider implementations + factory + router
├── ia/                      # Rule-based prediction & pattern detection
├── utils/                   # Theme, session, cache, exporters
└── views/                   # PySide6 UI pages (15+)
```

---

## 🚀 Getting started

```bash
# Clone the repository
git clone https://github.com/<your-username>/digital-twin.git
cd digital-twin

# Install dependencies
pip install -r requirements.txt

# Configure your environment
cp .env.example .env
# Add your API keys (Gemini, Claude, Grok) or configure Ollama locally

# Run the app
python main.py
```

### Required environment variables

```env
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GROK_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434
```

> Ollama runs fully local — no API key required if you only want to test with it.




## 🙋 About

Built as a personal project to explore AI integration, multi-LLM architecture, and production-quality software design.

If you'd like to talk about the architecture, the memory system, or anything else in this project, feel free to reach out.
