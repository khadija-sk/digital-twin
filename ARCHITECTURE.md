# Architecture de l'Application Digital Twin

## Vue d'ensemble

Application de productivité personnelle avec assistant IA, suivi d'habitudes, gestion d'objectifs et analyse comportementale. Interface PySide6, base SQLite, multi-LLM (Gemini, Claude, Grok, Ollama).

---

## 1. Stack Technique

| Technologie | Version | Rôle |
|---|---|---|
| **Python** | ≥ 3.10 | Langage hôte |
| **PySide6** | ≥ 6.5.0 | Framework GUI Qt |
| **SQLAlchemy** | ≥ 2.0.0 | ORM / accès base de données |
| **SQLite** | — | Base de données embarquée |
| **bcrypt** | ≥ 4.0.0 | Hachage des mots de passe |
| **python-dotenv** | ≥ 1.0.0 | Configuration via `.env` |
| **google-genai** | ≥ 2.8.0 | Client Google Gemini |
| **anthropic** | ≥ 0.49.0 | Client Anthropic Claude |
| **requests** | (stdlib) | Client HTTP pour Ollama, Grok, DuckDuckGo |
| **numpy** | ≥ 1.24.0 | Calcul cosine similarity, embeddings |
| **plyer** | ≥ 2.0.0 | Notifications système |
| **pygame** | ≥ 2.5.0 | Sons (timer Pomodoro) |
| **fpdf2** | ≥ 2.7.0 | Export PDF |
| **python-docx** | ≥ 1.1.0 | Export DOCX |
| **speech_recognition** | — | Reconnaissance vocale (optionnel) |
| **sounddevice** | — | Capture audio (optionnel) |
| **PySide6.QtTextToSpeech** | — | Synthèse vocale (optionnel) |

---

## 2. Structure du Projet

```
DIGITAL_TWIN/
├── main.py                         # Point d'entrée — MainWindow, routage, bootstrap
├── .env                            # Clés API et configuration LLM
├── requirements.txt                # Dépendances Python
├── digital_twin.db                 # Base SQLite (ignorée par git)
│
├── models/                         # Modèles SQLAlchemy (ORM)
│   ├── database.py                 # Engine, session factory, init_db()
│   ├── user.py                     # Utilisateur
│   ├── daily_log.py                # Check-in quotidien
│   ├── study_session.py            # Session Pomodoro
│   ├── journal.py                  # Journal intime
│   ├── objective.py                # Objectifs
│   ├── badge.py                    # Badges (gamification)
│   ├── user_preference.py          # Préférences (thème, notifications)
│   └── extensions.py               # Modèles étendus (mémoire, cours, événements...)
│
├── controllers/                    # Logique métier
│   ├── auth_controller.py          # Inscription, connexion, reset password
│   ├── ai_controller.py            # Orchestrateur IA (chat, routage, fallbacks)
│   ├── llm_controller.py           # Contrôleur central multi-provider LLM
│   ├── checkin_controller.py       # Check-in CRUD, score, streak
│   ├── goals_controller.py         # Objectifs CRUD, progression
│   ├── journal_controller.py       # Journal CRUD, streaks
│   ├── timer_controller.py         # Timer Pomodoro
│   ├── gamification_controller.py  # XP, niveaux, badges
│   ├── preferences_controller.py   # Thème, notifications
│   ├── notification_controller.py  # Notifications bureau (plyer)
│   └── search_controller.py        # Recherche full-text
│
├── services/                       # Services avancés
│   ├── memory_system.py            # Mémoire persistante avec embeddings
│   ├── journal_analyzer.py         # Analyse de journal (sentiment, topics)
│   ├── emotion_detector.py         # Détection émotionnelle
│   ├── academic_service.py         # Gestion académique (cours, devoirs)
│   ├── smart_planner.py            # Planificateur intelligent
│   ├── recommendation_engine.py    # Recommandations adaptatives
│   ├── briefing_service.py         # Briefing quotidien
│   ├── profile_service.py          # Profil utilisateur (intérêts, traits)
│   ├── timeline_service.py         # Gestion d'événements
│   ├── analytics_service.py        # Analyse complète (productivité, humeur...)
│   ├── smart_goals_service.py      # Objectifs avec insights IA
│   ├── unified_calendar_service.py # Calendrier unifié
│   ├── voice_service.py            # Synthèse et reconnaissance vocale
│   ├── web_search_service.py       # Recherche web DuckDuckGo
│   ├── context_retriever.py        # Agrégation de contexte utilisateur
│   ├── conversation_manager.py     # Gestion d'historique de chat
│   ├── prompt_builder.py           # Construction de prompts système
│   ├── config_service.py           # Lecture/écriture de la configuration .env
│   ├── model_manager.py            # Découverte et sélection de modèles
│   ├── gemini_service.py           # Wrapper Gemini
│   ├── anthropic_service.py        # Wrapper Claude
│   └── llm/                        # Implémentations des providers LLM
│       ├── base_provider.py        # Classe abstraite + dataclasses
│       ├── gemini_provider.py      # Google Gemini
│       ├── anthropic_provider.py   # Anthropic Claude
│       ├── ollama_provider.py      # Ollama (local)
│       ├── grok_provider.py        # xAI Grok
│       ├── provider_factory.py     # Factory pattern
│       └── question_router.py      # Routage de questions par complexité
│
├── ia/                             # Modules IA historiques (basés sur règles)
│   ├── predictor.py                # Prédiction score / risque burnout
│   ├── pattern_detector.py         # Détection de patterns (burnout, corrélations)
│   └── routine_suggester.py        # Suggestion de routine quotidienne
│
├── utils/                          # Utilitaires partagés
│   ├── theme.py                    # Palettes couleurs, Theme class, stylesheet
│   ├── session.py                  # Gestion de session avec timeout
│   ├── cache.py                    # Cache TTL
│   ├── sound_manager.py            # Sons (pygame)
│   ├── quote_manager.py            # Citations motivationnelles
│   ├── csv_exporter.py             # Export CSV
│   ├── pdf_exporter.py             # Export PDF (fpdf2)
│   ├── docx_exporter.py            # Export DOCX
│   └── txt_exporter.py             # Export TXT
│
└── views/                          # Interface utilisateur PySide6
    ├── login_view.py               # Connexion / inscription
    ├── onboarding_view.py          # Onboarding + rapport hebdo
    ├── home_view.py                # Accueil (StatCards, ActionCards)
    ├── sidebar_widget.py           # Barre latérale de navigation
    ├── dashboard_view.py           # Tableau de bord
    ├── checkin_view.py             # Check-in quotidien
    ├── timer_view.py               # Timer Pomodoro
    ├── stats_view.py               # Statistiques
    ├── goals_view.py               # Objectifs
    ├── journal_view.py             # Journal
    ├── ai_view.py                  # Chat IA complet
    ├── ai_panel.py                 # Chat IA latéral (mini)
    ├── profile_view.py             # Profil utilisateur
    ├── routine_view.py             # Routine suggérée
    ├── search_view.py              # Recherche globale
    ├── health_view.py              # Santé
    ├── settings_view.py            # Paramètres (multi-onglets)
    ├── briefing_view.py            # Briefing quotidien
    ├── recommendations_view.py     # Recommandations + défi journalier
    ├── analytics_view.py           # Analytics (radar chart custom)
    ├── calendar_view.py            # Calendrier unifié
    ├── academic_view.py            # Gestion académique
    ├── timeline_view.py            # Frise chronologique
    ├── profile_insights_view.py    # Intérêts et traits
    ├── heatmap_widget.py           # Carte de chaleur (QPainter)
    ├── spinner_widget.py           # Spinner de chargement
    ├── toast_notification.py       # Notifications toast
    ├── badge_popup.py              # Déverrouillage de badge
    ├── model_selector_widget.py    # Sélecteur de modèle LLM
    └── robot_avatar.py             # Avatar robot animé
```

---

## 3. Modèles de Données (SQLAlchemy)

### Modèles Principaux

| Modèle | Table | Champs clés |
|---|---|---|
| `User` | `users` | id, nom, email, password_hash, xp_total, niveau, reset_token |
| `DailyLog` | `daily_logs` | id, utilisateur_id, date, humeur(1-5), energie(1-5), sommeil(h), score_productivite |
| `StudySession` | `study_sessions` | id, utilisateur_id, date_heure_debut, duree(min), statut, energie_mi_session |
| `Journal` | `journals` | id, utilisateur_id, date, contenu(Text) |
| `Objective` | `objectives` | id, utilisateur_id, description, valeur_cible, statut(actif/atteint) |
| `Badge` | `badges` | id, utilisateur_id, nom, xp_gagne, icone |
| `UserPreference` | `user_preferences` | id, utilisateur_id, theme, notif_*, onboarding_complete |

### Modèles Étendus (`extensions.py`)

| Modèle | Rôle | Champs clés |
|---|---|---|
| `MemoryEntry` | Mémoire persistante avec embeddings | content, category, memory_type, embedding(JSON), importance |
| `MemorySummary` | Résumé périodique de mémoire | summary, period_start, period_end, category |
| `AcademicCourse` | Cours académique | name, code, credits, grade, status |
| `AcademicAssignment` | Devoir académique | title, due_date, completed, grade, priority |
| `StudySubject` | Matière d'étude | name, total_hours, last_studied |
| `TimelineEvent` | Événement chronologique | event_type, title, icon, event_date, importance |
| `UserInterest` | Centre d'intérêt | name, category, weight |

Tous les modèles sont enregistrés dans `database.py:init_db()` via `Base.metadata.create_all()`.

---

## 4. Contrôleurs

### AuthController
- `register(nom, email, password)` → crée User + UserPreference
- `login(email, password)` → vérifie bcrypt, crée session
- `request_password_reset(email)` → génère token 15min
- `reset_password(token, new_password)` → vérifie token et réinitialise

### AIController
- `chat(question, user_id)` — point d'entrée principal du chat IA
  1. Tente le provider hash-balancé (Gemini si hash pair, Grok si impair)
  2. Si échec, tente le provider actif
  3. Si échec, utilise le QuestionRouter pour router par type
  4. Si échec, essaie tous les providers disponibles dans l'ordre
  5. Si tout échoue, réponse règle basée sur mots-clés
- `get_daily_insight(user_id)` → insight généré par LLM
- `route_question_type(question)` → utilise la question router

### LLMController (Singleton)
- `get_instance()` → retourne l'instance unique
- `configure(api_key, model_name)` → configure Gemini
- `configure_anthropic(api_key, model_name)`, `configure_ollama(host, model)`, `configure_grok(api_key, model)`
- `generate_content(prompt)` → génération synchrone via le provider actif
- `chat(system_prompt, message, history)` → chat streamé
- Propriétés: `active_provider`, `is_available`, `available_providers`

### Autres contrôleurs
| Contrôleur | Fonctionnalités |
|---|---|
| `CheckinController` | CRUD check-in, calcul score, streak, détection burnout |
| `GoalsController` | CRUD objectifs, calcul progression |
| `JournalController` | CRUD journal, streaks |
| `TimerController` | Logique timer Pomodoro, tick, sauvegarde sessions |
| `GamificationController` | XP, niveaux (1-5), badges (streak, Pomodoro milestones) |
| `PreferencesController` | Thème, notifications, onboarding |
| `NotificationController` | Notifications bureau via plyer |
| `SearchController` | Recherche full-text (journaux, objectifs, check-ins) |

---

## 5. Services - Fonctionnalités Avancées

### Services IA et Mémoire
| Service | Méthodes principales |
|---|---|
| **MemorySystem** | `store()`, `retrieve()` (cosine similarity), `search_by_keyword()`, `get_summary()`, `get_context_for_prompt()`, `update_importance()`, `get_timeline_events()` |
| **JournalAnalyzer** | `analyze_entry()` (sentiment, topics, stress, motivation), `get_recent_analyses()`, `generate_summary()` |
| **EmotionDetector** | `get_emotion_state()` (happiness, stress, motivation, burnout_risk, stability), `get_emotion_trend()` |
| **ContextRetriever** | `get_complete_context()`, `get_rag_context()` — agrège profil + logs + sessions + journals + objectifs + badges + mémoires |
| **PromptBuilder** | `build_system_prompt()`, `build_insight_prompt()` — prompts système riches avec contexte utilisateur |
| **ConversationManager** | Gestion historique chat, troncature, estimation tokens |

### Services Productivité
| Service | Méthodes principales |
|---|---|
| **SmartPlanner** | `get_today_plan()`, `get_weekly_schedule()`, `suggest_focus_time()`, `get_productivity_insights()` |
| **SmartGoalsService** | `get_goals_with_insights()`, `celebrate_milestone()`, `get_inactive_goals()` |
| **AnalyticsService** | `full_analysis()`, `productivity_analysis()`, `mood_analysis()`, `topic_analysis()`, `habit_analysis()`, `get_focus_stats()` |
| **BriefingService** | `generate_briefing()` — streak, comparaison hier, stats semaine, alertes deadlines, recommandations |
| **RecommendationEngine** | `get_recommendations()`, `get_daily_challenge()` — adaptés à l'état émotionnel |

### Services Spécialisés
| Service | Fonctionnalités |
|---|---|
| **AcademicService** | CRUD cours/devoirs/matières, taux de préparation examens |
| **ProfileService** | Tracking d'intérêts depuis le chat, traits (style communication, polyvalence) |
| **TimelineService** | Gestion d'événements avec icônes, grouping par jour, auto-import check-ins |
| **UnifiedCalendarService** | Fusion événements (devoirs + timeline + objectifs + sessions) en liste triée |
| **WebSearchService** | Recherche DuckDuckGo (API + fallback HTML), pas de clé API nécessaire |
| **VoiceService** | TTS via QTextToSpeech, STT via speech_recognition + sounddevice fallback |

### Services LLM (Providers)
| Provider | Méthodes clés |
|---|---|
| **GeminiProvider** | `chat()`, `chat_stream()`, `generate_content()`, `generate_embeddings()`, `discover_models()` |
| **AnthropicProvider** | `chat()`, `chat_stream()`, `generate_content()`, `generate_embeddings()`, `discover_models()` |
| **OllamaProvider** | `chat()`, `chat_stream()`, `generate_content()`, `generate_embeddings()`, `verify_connection()` |
| **GrokProvider** | `chat()`, `chat_stream()`, `generate_content()`, `verify_connection()` |
| **ProviderFactory** | `register()`, `create()`, `supported_providers()` |
| **QuestionRouter** | `route()` → 5 routes : general, complex, code, creative, data |

### ConfigService (Singleton)
- `initialize()` / `get_instance()`
- Getters/setters pour toutes les clés API, modèles, hôtes
- Persistance dans `.env`

---

## 6. Vues et Interface

### Système de Navigation

```
MainWindow
├── SidebarWidget (gauche, fixe 240px)
│   ├── Logo + titre
│   ├── NAV_ITEMS (15 entrées cliquables avec icônes)
│   ├── Theme toggle (🌙/☀️)
│   └── Logout button
│
├── ContentWrap (droite)
│   ├── TopBar (titre de page + bouton paramètres)
│   └── QStackedWidget
│       ├── LoginView (non connecté)
│       ├── HomeView / DashboardView / CheckinView / TimerView / ...
│       └── ... (15+ vues enregistrées dynamiquement)
│
└── AIPanel (panneau latéral droit, toggleable)
```

**Flux de navigation :**
1. Clic sur un item de la sidebar → `on_navigate(page_name)`
2. `MainWindow._navigate(page)` :
   - Si la page est déjà dans `self._pages` → appelle `refresh()` et `load_data()`, transition fade
   - Sinon → `_create_page(page)` instancie la vue, l'ajoute au stack, transition fade
3. `_create_page()` est un if-elif chaîne de 15+ branches
4. Les vues sont mises en cache dans `self._pages` pour les navigations rapides

### Liste des Pages Accessibles

| Page | Vue | Description |
|---|---|---|
| `home` | HomeView | Accueil avec stat cards + action cards + barre XP |
| `dashboard` | DashboardView | Tableau de bord avec résumés |
| `checkin` | CheckinView | Formulaire check-in (humeur, énergie, sommeil) |
| `timer` | TimerView | Timer Pomodoro (50/16 min) |
| `stats` | StatsView | Statistiques |
| `goals` | GoalsView | Gestion d'objectifs avec barres de progression |
| `journal` | JournalView | Journal intime avec streak |
| `ai` | AIView | Chat IA complet avec streaming, web search, voice |
| `profile` | ProfileView | Profil utilisateur |
| `routine` | RoutineView | Suggestion de routine |
| `search` | SearchView | Recherche globale |
| `health` | HealthView | Suivi santé |
| `briefing` | BriefingView | Briefing quotidien |
| `recommendations` | RecommendationsView | Recommandations + défi |
| `analytics` | AnalyticsView | Radar chart + stats + recommandations |
| `calendar` | CalendarView | Calendrier unifié mois |
| `settings` | SettingsView | Paramètres (profile, AI, export, backup) |
| `academic` | AcademicView | Cours, devoirs, préparation examens |
| `timeline` | TimelineView | Frise chronologique |
| `profile_insights` | ProfileInsightsView | Intérêts et traits |

### Vues avec QThread Loading
Les vues qui chargent des données utilisent des workers QThread pour ne pas bloquer l'UI :
- `AIView` → `AIWorker`, `StreamWorker`, `WebSearchWorker`
- `AnalyticsView` → `AnalyticsLoader`
- `BriefingView` → `BriefingLoader`
- `CalendarView` → `CalendarLoader`
- `AcademicView` → `AcademicLoader`
- `TimelineView` → `TimelineLoader`
- `RecommendationsView` → `RecommendationLoader`
- `ProfileInsightsView` → `ProfileLoader`

### Widgets Réutilisables
| Widget | Fichier | Description |
|---|---|---|
| `SidebarWidget` | `sidebar_widget.py` | Barre latérale avec scroll, QScroller |
| `StatCard` / `ActionCard` | `home_view.py` | Cartes d'accueil |
| `HeatmapWidget` | `heatmap_widget.py` | Carte de chaleur 365 jours (QPainter) |
| `SpinnerWidget` | `spinner_widget.py` | Overlay de chargement |
| `ToastNotification` | `toast_notification.py` | Notification popup flottante |
| `BadgePopup` | `badge_popup.py` | Animation de déblocage de badge |
| `ModelSelectorWidget` | `model_selector_widget.py` | Dropdown de sélection de modèle LLM |
| `RobotAvatar` | `robot_avatar.py` | Avatar robot animé |
| `MessageBubble` | `ai_panel.py` | Bulle de message chat |

---

## 7. Système de Thème

### Palettes (`utils/theme.py`)

**Sombre (défaut) :**
```
BG            #1B1613  (Dark Chocolate)
Sidebar       #241D1A  (Espresso)
Cards         #2F2723  (Walnut)
Accent        #E8A5B5  (Sakura Pink)
Text Primary  #F7F3EF  (Ivory)
Text Secondary #CFC6BE (Soft Beige)
Text Muted    #8B827A  (Gray)
```

**Clair :**
- Variante inversée avec fond beige clair et texte foncé

### Classe Theme
- `colors()` → dictionnaire de la palette active
- `get(key)` → valeur spécifique
- `stylesheet()` → QSS complet de l'application
- `glass_card()` / `card_hover_effect()` → styles verre dépoli
- `set_palette(palette_name)` / `get_palette()` → changement dynamique

### Flux de changement de thème
1. Clic 🌙/☀️ dans sidebar → `window()._on_theme_changed()`
2. `_on_theme_changed()` → appelle `Theme.set_palette()`, réapplique le stylesheet global
3. Parcourt toutes les pages + sidebar + AI panel + appelle `refresh_theme()` sur chaque

### Utilisation dans les vues
```python
c = Theme.colors()
style = f"""
    QWidget {{ color: {c["TEXT_PRIMARY"]}; background-color: {c["BG"]}; }}
    QFrame#card {{ background: {c["CARD_BG"]}; border-radius: 12px; }}
"""
```

---

## 8. Intégration LLM (Multi-Provider)

### Architecture
```
                    ┌─────────────────────────┐
                    │     LLMController        │
                    │     (Singleton)           │
                    └─────────┬───────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                  │
    ┌───────▼───────┐ ┌──────▼───────┐  ┌──────▼───────┐
    │ GeminiProvider│ │GrokProvider  │  │OllamaProvider│  ...
    │ (google-genai)│ │ (requests)   │  │ (requests)   │
    └───────────────┘ └───────────────┘  └───────────────┘
```

### Routage Intelligent (`AIController`)
1. **Hash balancing** → `sha256(question) % 2` choisit entre Gemini et Grok
2. **QuestionRouter** → 5 routes: `general`, `complex`, `code`, `creative`, `data`
3. **Fallback chaîne** → si le provider actif échoue, essaie tous les autres providers dans l'ordre
4. **Fallback règles** → si tout LLM échoue, réponse basée sur des patterns regex

### Construction du Contexte
`ContextRetriever` agrège :
- Profil utilisateur
- Derniers check-ins (7 jours)
- Dernières sessions d'étude
- Derniers journaux
- Mémoires persistantes (via MemorySystem.retrieve)
- Objectifs actifs
- Badges

→ Transmis à `PromptBuilder.build_system_prompt()` pour générer un prompt système riche.

---

## 9. Base de Données

- **Moteur** : SQLite (`digital_twin.db`)
- **Connexion** : `create_engine("sqlite:///...", connect_args={"check_same_thread": False})` pour support multithread
- **Session** : `get_session()` → session SQLAlchemy, à fermer avec `session.close()` dans `finally`
- **Initialisation** : `init_db()` crée toutes les tables + exécute des migrations ALTER TABLE pour l'évolution du schéma
- **Backup/Restore** : `shutil.copy2()` dans SettingsView

---

## 10. Patterns Architecturaux Clés

### Singleton
- `LLMController` — gestion centralisée des providers LLM
- `ConfigService` — configuration .env
- `SessionManager` — session utilisateur avec timeout
- `AIService` / `AnthropicService` — wrappers legacy

### Factory
- `ProviderFactory` — création de providers LLM par nom

### Observer (Signals/Slots)
- Navigation : clic sidebar → signal → `_navigate()`
- QThread workers : `done` signal → mise à jour UI
- Check-in : `checkin_done` signal → rafraîchissement dashboard

### QThread Workers
Pattern pour le chargement asynchrone :
```python
class MonLoader(QThread):
    done = Signal(list)

    def run(self):
        result = service.get_data()
        self.done.emit(result)

# Dans la vue :
self._loader = MonLoader(user_id)
self._loader.done.connect(self._on_data_ready)
self._loader.start()
```

⚠️ **Important** : Ne jamais appeler `deleteLater()` sur un QThread en cours d'exécution (« QThread: Destroyed while thread is still running » → crash). Pattern utilisé : stocker le thread dans `self._loader`, déconnecter les signaux, laisser le thread se terminer naturellement.

### Gestion des Erreurs
- `sys.excepthook` redirigé (pas de popup traceback)
- Tous les workers QThread ont des `try/except` avec émission de valeurs par défaut
- Services de suggestion utilisent des fallbacks (ex: `ROUTINE_FALLBACK` si LLM indisponible)

---

## 11. Dépendances Externes

### Bibliothèques Principales (requirements.txt)
```
PySide6>=6.5.0
SQLAlchemy>=2.0.0
bcrypt>=4.0.0
plyer>=2.0.0
pygame>=2.5.0
numpy>=1.24.0
google-genai>=2.8.0
python-dotenv>=1.0.0
fpdf2>=2.7.0
python-docx>=1.1.0
anthropic>=0.49.0
```

### Bibliothèques Optionnelles (importées, pas dans requirements)
- `requests` — HTTP (stdlib, généralement pré-installé)
- `speech_recognition` — STT vocal
- `sounddevice` — capture audio
- `PySide6.QtTextToSpeech` — TTS (inclus avec PySide6)

---

## 12. Fonctionnalités Détaillées

### Mémoire Persistante (MemorySystem)
- Stockage d'entrées mémoire avec embeddings (vecteurs JSON)
- Recherche par similarité cosine
- Auto-trimming des entrées peu importantes
- Résumé périodique
- Timeline extraction

### Gamification
- XP gagné par : check-in, sessions Pomodoro, streaks
- Niveaux 1-5 avec seuils progressifs
- Badges : « 7 jours streak », « 50 Pomodoros », etc.
- Popup de déblocage animée

### Exports
| Format | Librairie | Contenu |
|---|---|---|
| CSV | csv (stdlib) | Check-ins, sessions, journaux |
| PDF | fpdf2 | Rapports formatés |
| DOCX | python-docx | Documents éditables |
| TXT | — | Export texte brut |

### Recherche Full-Text
Recherche dans : journaux, objectifs, check-ins (date, humeur, énergie)

### Voix
- TTS : `QTextToSpeech` (synthèse vocale Windows/macOS)
- STT : `speech_recognition` (API Google gratuite) + `sounddevice` fallback

### Backup/Restore
- Backup : copie de `digital_twin.db` vers chemin choisi
- Restore : remplacement de la base et redémarrage de l'application

---

## 13. Glossaire

| Terme | Définition |
|---|---|
| **LLM** | Large Language Model (Gemini, Claude, Grok, Ollama) |
| **Provider** | Fournisseur LLM (GeminiProvider, GrokProvider...) |
| **QThread** | Thread Qt pour opérations asynchrones |
| **QSS** | Qt Stylesheet (CSS-like pour widgets Qt) |
| **RAG** | Retrieval-Augmented Generation (contexte injecté dans le prompt) |
| **Check-in** | Saisie quotidienne humeur/énergie/sommeil |
| **Pomodoro** | Session de travail de 50 min (configurable) |
| **XP** | Points d'expérience pour la gamification |
| **Streak** | Nombre de jours consécutifs d'activité |
| **Cosine Similarity** | Mesure de similarité entre vecteurs d'embedding |
| **Embedding** | Représentation vectorielle d'un texte |

---

*Document généré le 20 juin 2026 — Projet Digital Twin*
