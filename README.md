# Digital Twin

> Your digital self — tracking and growing with you.

An AI-powered personal productivity desktop application that combines **habit tracking, journaling, goal management, academic tools, and persistent AI memory** into one application.

Built with **PySide6**, **SQLAlchemy**, and a multi-provider LLM architecture supporting **Gemini, Grok, Claude, and Ollama**.

---

## Why this project

Most AI assistants treat each conversation as an isolated session.

Digital Twin explores a different approach: combining daily habits, goals, journal entries, study sessions, and academic progress into a persistent personal context that can be used across conversations.

The goal is to create an assistant that can understand the user's ongoing activities rather than responding only to the current message.

---

## Core Features

### AI & Persistent Memory

* **Persistent memory system** storing information with embeddings
* Similarity-based memory retrieval using **cosine similarity**
* **ContextRetriever** that aggregates:

  * User profile
  * Daily logs
  * Study sessions
  * Journal entries
  * Goals
  * Stored memories
* Shared prompt builder used across LLM providers
* **Multi-LLM architecture** supporting:

  * Gemini
  * Grok
  * Claude
  * Ollama
* Provider fallback mechanism
* **Question router** for different query types:

  * General
  * Complex
  * Code
  * Creative
  * Data
* Web search integration using **DuckDuckGo**
* Voice interaction:

  * Speech-to-Text
  * Text-to-Speech

### Productivity

* Daily check-ins for:

  * Mood
  * Energy
  * Sleep
* Streak tracking
* Pomodoro timer with session history
* Goal management
* AI-generated goal subtasks
* Goal progress tracking
* Inactivity detection
* AI-assisted journal analysis
* Unified calendar for:

  * Assignments
  * Goals
  * Timeline events
  * Study sessions
* Academic tracking for courses and assignments
* Exam preparation readiness

### Insights & Analytics

* Daily productivity briefing
* Productivity and behavior trends
* Next-day productivity prediction
* Personalized recommendations
* Daily challenges based on user activity
* Gamification system:

  * XP
  * Levels
  * Streaks
  * Badges
* Radar-chart analytics covering:

  * Productivity
  * Mood
  * Energy
  * Sleep
  * Consistency
  * Study sessions
* Exportable reports:

  * PDF
  * DOCX
  * CSV
  * TXT

### Interface

* 15+ application pages
* Sidebar-based navigation
* Light and dark themes
* Toast notifications
* Loading states
* Animated badge unlocks

---

## Architecture

```text
┌─────────────────────┐         ┌─────────────────────┐
│  Interface (PySide6)│         │   AI Panel (Chat)    │
└──────────┬───────────┘         └──────────┬──────────┘
           │                                 │
           └───────────────┬─────────────────┘
                           ▼
              ┌─────────────────────────┐
              │   Application Layer     │
              │ Controllers & Services  │
              └─────────────┬───────────┘
                            ▼
        ┌───────────┬───────────────┬───────────────┐
        │  Service  │    AI Engine  │  Data Access  │
        │   Layer   │ ContextRetriever│    Layer    │
        │           │ PromptBuilder   │ SQLAlchemy   │
        │           │ ProviderFactory │              │
        └───────────┴───────────────┴───────────────┘
                            ▼
        ┌─────────┬─────────┬─────────┬─────────┐
        │ Gemini  │  Grok   │ Claude  │ Ollama  │
        └─────────┴─────────┴─────────┴─────────┘
                            ▼
                  ┌──────────────────┐
                  │ SQLite Database  │
                  └──────────────────┘
```

A detailed architecture diagram is available in:

[`docs/architecture.png`](https://github.com/khadija-sk/digital-twin/blob/main/docs/architecture.png)

---

## Tech Stack

| Layer                   | Technology                                    |
| ----------------------- | --------------------------------------------- |
| UI                      | PySide6 / Qt6                                 |
| ORM / Database          | SQLAlchemy + SQLite                           |
| Authentication          | bcrypt                                        |
| LLM Providers           | Google Gemini, Anthropic Claude, Grok, Ollama |
| Embeddings / Similarity | NumPy                                         |
| PDF Export              | fpdf2                                         |
| DOCX Export             | python-docx                                   |
| Notifications           | plyer                                         |
| Sound                   | pygame                                        |
| Speech Recognition      | speech_recognition                            |
| Audio Input             | sounddevice                                   |
| Text-to-Speech          | QtTextToSpeech                                |

---

## Project Structure

```text
digital_twin/
├── main.py
│
├── models/
│   └── SQLAlchemy ORM models
│
├── controllers/
│   └── Authentication, AI, Goals, Journal, Timer, LLM...
│
├── services/
│   ├── Memory
│   ├── Analytics
│   ├── Planning
│   ├── Prompt Building
│   └── LLM Providers
│       └── Provider implementations, factory and router
│
├── ia/
│   └── Prediction and pattern detection
│
├── utils/
│   └── Themes, sessions, cache and exporters
│
├── views/
│   └── PySide6 UI pages
│
├── docs/
│   └── architecture.png
│
└── requirements.txt
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/khadija-sk/digital-twin.git
cd digital-twin
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file based on `.env.example`:

```text
GEMINI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GROK_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434
```

API keys are only required for the corresponding cloud providers.

**Ollama** can be used locally without a cloud API key.

### 4. Run the application

```bash
python main.py
```

---

## LLM Architecture

Digital Twin uses a provider-based architecture instead of coupling the application to a single LLM.

```text
                    User Query
                        │
                        ▼
                 Question Router
                        │
                        ▼
                Provider Factory
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Gemini          Grok        Claude/Ollama
          │             │             │
          └─────────────┼─────────────┘
                        ▼
                  Generated Response
```

The architecture makes it possible to switch between providers while keeping the application logic independent from a specific LLM API.

---

## Persistent Memory

The memory system is one of the central components of the application.

Information from different parts of the application can be converted into embeddings and stored for later retrieval.

When a user asks a question, the system can retrieve semantically similar memories using **cosine similarity** and combine them with the current application context.

```text
User Data
    │
    ├── Profile
    ├── Journal
    ├── Goals
    ├── Study Sessions
    └── Daily Logs
            │
            ▼
       Embeddings
            │
            ▼
      Memory Storage
            │
            ▼
    Similarity Retrieval
            │
            ▼
     Context Retriever
            │
            ▼
        LLM Prompt
```

---

## About the Project

Digital Twin is a personal project developed to explore:

* AI application development
* Multi-LLM architectures
* Persistent AI memory
* Semantic retrieval
* Desktop application development
* Data-driven productivity tools
* Software architecture and modular design

The project brings together AI, data, software engineering, and productivity into a single desktop application.

---

## Author

**Khadija Sayoukh**

Engineering Student — Digital Transformation & Artificial Intelligence

[GitHub](https://github.com/khadija-sk) · [LinkedIn](https://www.linkedin.com/in/khadija-sayoukh-1a1a94288)
