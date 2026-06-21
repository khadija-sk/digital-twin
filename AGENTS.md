## Goal
- Extend the Digital Twin PySide6 app with advanced AI features (memory, emotion detection, predictions, recommendations, academic assistant, planner, file intelligence, timeline, daily briefing, profile insights) while preserving all existing functionality.

## Constraints & Preferences
- Do NOT rebuild or replace existing features
- Keep existing project structure; follow SOLID principles, modular design, production-quality code
- Reuse existing services when possible; avoid duplicate code
- User prefers French UI; app already partially translated
- User specified exact dark mode palette colors (Dark Chocolate #1B1613, Espresso #241D1A, Walnut #2F2723, Sakura Pink #E8A5B5, Milk Tea #D7B89E, Aloewood #8A6A55, Ivory #F7F3EF, Soft Beige #CFC6BE, Gray #8B827A)
- App must handle all errors gracefully (no raw Python traceback popups)
- All new files must pass Python syntax validation before being declared done
- Do NOT modify existing view files except for imports, sidebar, and navigation wiring in main.py

## Progress
### Done
- **8 new services** in `services/`:
  - `memory_system.py` — embedding-based memory with SQLite storage, cosine similarity ranking, auto-trimming, summarization, timeline extraction
  - `journal_analyzer.py` — sentiment analysis via keyword matching, topic extraction (9 categories), summary generation
  - `emotion_detector.py` — happiness/stress/motivation/burnout_risk/stability from DailyLog data with trend analysis
  - `academic_service.py` — CRUD for courses, assignments, study subjects; exam readiness %, upcoming deadlines
  - `smart_planner.py` — today's plan, weekly schedule, focus time suggestion, productivity insights with correlations
  - `recommendation_engine.py` — adaptive recommendations + daily challenges based on emotional state and interests
  - `briefing_service.py` — daily briefing with streak, week stats, yesterday comparison, deadline alerts, wellness recs
  - `profile_service.py` — interest tracking from chat, user traits (communication style, versatility)
  - `file_intelligence.py` — file analysis for PDF/DOCX/PPTX/TXT/images; batch directory import
  - `timeline_service.py` — event management with icons, day grouping, auto-import from daily logs

- **10 new views** in `views/`:
  - `briefing_view.py` — BriefingView + EmptyStateView
  - `emotion_view.py` — EmotionView with QThread loader, stat cards, trend display
  - `academic_view.py` — AcademicView with readiness bar, QThread loader
  - `timeline_view.py` — TimelineView with day-grouped events, QThread loader
  - `recommendations_view.py` — RecommendationsView with daily challenge, priority cards, QThread loader
  - `profile_insights_view.py` — ProfileInsightsView with stats + interest chips, QThread loader
  - `planner_view.py` — PlannerView with today's plan, week stats, insights, QThread loader
  - `files_view.py` — FilesView with import file/dir buttons, dynamic result cards

- **Database models** in `models/extensions.py`: MemoryEntry, MemorySummary, AcademicCourse, AcademicAssignment, StudySubject, TimelineEvent, UserInterest — registered in `database.py:init_db()`

- **Sidebar navigation**: 8 new items (Briefing, Émotions, Planner, Fichiers, Campus, Timeline, Recommandations, Intérêts)

- **main.py**: Imports all new views, routes them in `_create_page()`, calls `load_data()` in `_navigate()`, added `_generate_briefing()`

### 2025-06-19 — Batch 2: 5 features
- **💾 Backup/Restore** — `views/settings_view.py`: new section with `_handle_backup()` (copies DB to user-chosen path) and `_handle_restore()` (replaces DB from backup, quits app). Uses `shutil.copy2()`.
- **📊 Heatmap d'habitudes** — `services/habits_heatmap_service.py`: aggregates DailyLog + StudySession + Objective into daily 0-10 scores, computes streak. `views/habits_view.py`: full-page view using existing `HeatmapWidget` (365-day grid) + stat cards grid. Loader: `HabitLoader`.
- **📅 Calendrier unifié** — `services/unified_calendar_service.py`: merges `AcademicAssignment` (deadlines), `TimelineEvent`, `Objective` (goals), `StudySession` (study days) into sorted event list. `views/calendar_view.py`: day-grouped view with prev/next/today nav, event cards with icon + source badge. Loader: `CalendarLoader`.
- **🔥 Focus Mode** — `views/focus_view.py`: embedded `TimerController` (start/pause/reset), progress bar, AI suggestion from `SmartPlanner`, focus analytics from `AnalyticsService.get_focus_stats()`. Loader: `FocusSuggestionLoader`.
- **🎯 Connexions IA** — `services/connections_service.py`: keyword matching between journals ↔ goals ↔ memories ↔ interests, plus optional LLM deep connection via `LLMController.chat()`. `views/connections_view.py`: card list with icon + relevance %. Loader: `ConnectionsLoader`.

### Done (Current)
- All 5 features implemented and wired
- **Sidebar**: 4 new items (Habitudes, Calendrier, Focus, Connexions) — 25 total
- **main.py**: routes for 4 new pages + titles
- `AnalyticsService.get_focus_stats()` added
- All files pass syntax validation

### In Progress
- (none)

### Blocked
- (none currently)

## Key Decisions
- All new AI features use LLM-based analysis via whichever provider is configured, not a separate ML stack
- Memory stored in SQLite with JSON-serialized embedding vectors; no separate vector DB needed
- New models go in `models/extensions.py`; services follow `services/*.py` pattern (no controllers needed)
- Views that fetch data use QThread loaders to keep UI responsive
- Views use `setup_style()` + `Theme.colors()` + `refresh_theme()` for dynamic theming

## Critical Context
- App uses PySide6, SQLAlchemy + SQLite, Python 3
- LLM providers: Gemini, Anthropic Claude, Ollama — via existing `LLMController` singleton
- `Theme.colors()` returns palette dict; `Theme.stylesheet()` returns full app QSS
- User's exact dark palette: BG #1B1613, Sidebar #241D1A, Cards #2F2723, Accent #E8A5B5, Text #F7F3EF, Secondary #CFC6BE, Muted #8B827A
- Existing features (login, home, dashboard, timer, stats, goals, journal, checkin, routine, search, health, AI chat, profile, settings) are untouched
