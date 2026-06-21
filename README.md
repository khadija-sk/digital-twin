# Digital Personal Twin

A PySide6 desktop application — your personal AI-powered digital twin for journaling, emotional tracking, academic planning, productivity, and self-improvement.

## Features

- **🧠 AI Chat** — Multi-provider LLM chat (Gemini, Claude, Ollama, Grok) with memory, context retrieval, and markdown rendering
- **📓 Journal** — Daily entries with AI-powered summary, sentiment analysis, and topic extraction
- **📊 Analytics & Stats** — Visual charts for mood, productivity, habits, and trends over time
- **🎯 Goals & Objectives** — Track goals with progress, streaks, and smart suggestions
- **📚 Academic Assistant** — Courses, assignments, study subjects, exam readiness tracking
- **📅 Unified Calendar** — Merged view of assignments, events, goals, and study sessions
- **🔥 Focus Mode** — Pomodoro timer with AI focus suggestions and analytics
- **💪 Habits Heatmap** — 365-day grid tracking daily habits, streaks, and consistency
- **📎 File Intelligence** — Analyze PDF, DOCX, PPTX, TXT, and image files
- **🧠 Memory System** — Embedding-based memory with auto-summarization and timeline extraction
- **😊 Emotion Detection** — Happiness, stress, motivation, burnout risk from daily logs
- **📋 Daily Briefing** — Streak tracking, week stats, deadline alerts, wellness recommendations
- **🔗 AI Connections** — Semantic links between journals, goals, memories, and interests
- **💾 Backup & Restore** — Full database backup and restore with file dialog
- **🎨 Dark Theme** — Custom dark palette (Dark Chocolate, Sakura Pink, Milk Tea, Ivory)

## Tech Stack

- **Python 3** + **PySide6** (Qt for Python)
- **SQLAlchemy** + **SQLite** for persistence
- Modular service-oriented architecture with QThread async loaders

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Configuration

Copy `.env.example` to `.env` and add your API keys:

```
GEMINI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

## Project Structure

```
├── controllers/        # Business logic controllers
├── ia/                 # Pattern detection, prediction
├── models/             # SQLAlchemy ORM models
├── services/           # AI services (memory, emotions, planner, etc.)
├── utils/              # Theme, exporters, cache, session
└── views/              # PySide6 UI views (25+ screens)
    ├── chat/           # Reusable chat components
    └── *.py            # Individual page views
```

## License

MIT
