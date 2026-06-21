from datetime import date


class PromptBuilder:

    SYSTEM_PROMPT_BASE = """Tu es un assistant IA généraliste, intelligent et utile. Tu réponds à TOUS les types de questions : productivité, technologie, science, culture, conseils, créativité, etc. Si des données personnelles de l'utilisateur sont fournies dans le contexte ci-dessous, utilise-les pour personnaliser ta réponse. Sinon, réponds avec tes connaissances générales.

Réponds toujours en français, quelle que soit la langue de la question."""

    WEEKLY_INSIGHT_PROMPT = (
        "Basé sur les données ci-dessus, donne un conseil personnalisé en 2-3 phrases maximum. "
        "Cite un chiffre précis. Sois encourageant."
    )

    JOURNAL_SUMMARY_PROMPT = (
        "Voici les entrées de journal de l'utilisateur pour la semaine. "
        "Fais un résumé bienveillant en 4-5 phrases : "
        "thèmes récurrents, évolution émotionnelle, et un conseil personnalisé. "
        "Cite des éléments précis des entrées."
    )

    ROUTINE_PROMPT = (
        "Basé sur les données de sommeil, d'énergie et d'humeur, "
        "propose une routine quotidienne idéale pour demain avec des créneaux horaires. "
        "Inclus des suggestions de travail (Pomodoro), pauses et activités de bien-être. "
        "Sois précis sur les horaires."
    )

    @classmethod
    def _format_profile_section(cls, profile: dict) -> str:
        if not profile:
            return ""
        return (
            f"## Profil Utilisateur\n"
            f"- Nom : {profile.get('name', 'N/A')}\n"
            f"- Niveau : {profile.get('level', 1)} ({profile.get('xp', 0)} XP)\n"
            f"- Check-ins : {profile.get('total_checkins', 0)} | "
            f"Sessions : {profile.get('total_sessions', 0)} | "
            f"Journal : {profile.get('total_journals', 0)} entrées\n"
        )

    @classmethod
    def _format_logs_section(cls, logs: dict) -> str:
        if not logs:
            return "## Comportement Récent\nPas encore de données de check-in.\n"
        lines = [f"## Comportement ({logs.get('period_days', 7)} derniers jours)"]
        lines.append(f"- Check-ins enregistrés : {logs.get('log_count', 0)}")
        lines.append(f"- Humeur moyenne : {logs.get('average_mood', 'N/A')}/5 ({logs.get('mood_trend', 'N/A')})")
        lines.append(f"- Énergie moyenne : {logs.get('average_energy', 'N/A')}/5 ({logs.get('energy_trend', 'N/A')})")
        lines.append(f"- Sommeil moyen : {logs.get('average_sleep', 'N/A')}h")
        score = logs.get('average_score')
        if score is not None:
            lines.append(f"- Score productivité moyen : {score}/100")
        trend = logs.get('score_trend')
        if trend and trend != 'insufficient_data':
            lines.append(f"- Tendance des scores : {'📈 Hausse' if trend == 'up' else '📉 Baisse' if trend == 'down' else '➡️ Stable'}")
        if logs.get('latest_score') is not None:
            lines.append(f"- Dernier score : {logs['latest_score']}/100")
        if logs.get('best_score') is not None:
            lines.append(f"- Meilleur score : {logs['best_score']}/100")
        if logs.get('burnout_risk'):
            lines.append("- ⚠️ RISQUE DE BURNOUT DÉTECTÉ (énergie en baisse)")
        scores_line = logs.get('scores', [])
        if scores_line:
            lines.append(f"- Scores bruts : {[s.get('score') for s in scores_line]}")
        return "\n".join(lines)

    @classmethod
    def _format_sessions_section(cls, sessions: dict) -> str:
        if not sessions or sessions.get("total_sessions", 0) == 0:
            return "## Sessions d'Étude\nAucune session Pomodoro récente.\n"
        return (
            f"## Sessions d'Étude (7 jours)\n"
            f"- Sessions complétées : {sessions.get('total_sessions', 0)}\n"
            f"- Temps total : {sessions.get('total_hours', 0)}h ({sessions.get('total_minutes', 0)} min)\n"
            f"- Durée moyenne : {sessions.get('average_duration', 0)} min/session\n"
        )

    @classmethod
    def _format_journals_section(cls, journals: list) -> str:
        if not journals:
            return "## Journal\nAucune entrée de journal récente.\n"
        lines = ["## Entrées de Journal"]
        for j in journals:
            content = j.get("content", "").replace("\n", " ").strip()
            lines.append(f"- [{j.get('date', 'N/A')}] {content}")
        return "\n".join(lines)

    @classmethod
    def _format_objectives_section(cls, objectives: list, stats: dict) -> str:
        if not objectives and stats:
            return (
                f"## Objectifs\n"
                f"- Actifs : {stats.get('active', 0)} | Atteints : {stats.get('achieved', 0)}\n"
            )
        lines = [f"## Objectifs Actifs ({len(objectives)})"]
        for obj in objectives:
            lines.append(f"- {obj.get('description', 'N/A')}")
        if stats:
            lines.append(f"Total : {stats.get('active', 0)} actifs, {stats.get('achieved', 0)} atteints")
        return "\n".join(lines)

    @classmethod
    def _format_badges_section(cls, badges: list) -> str:
        if not badges:
            return ""
        lines = ["## Badges et Récompenses"]
        for b in badges:
            lines.append(f"- {b.get('icon', '🏅')} {b.get('name', 'N/A')} ({b.get('date', 'N/A')})")
        return "\n".join(lines)

    @classmethod
    def _format_journal_hits(cls, hits: list) -> str:
        if not hits:
            return ""
        lines = ["## Entrées de Journal Pertinentes (RAG)"]
        for h in hits:
            content = h.get("content", "").replace("\n", " ").strip()
            lines.append(f"- [{h.get('date', 'N/A')}] (score: {h.get('relevance', 0)}) {content}")
        return "\n".join(lines)

    @classmethod
    def _format_memories_section(cls, memories: list[dict]) -> str:
        if not memories:
            return ""
        lines = ["## Souvenirs Récents (ce que tu as partagé précédemment)"]
        for m in memories:
            lines.append(f"- ({m.get('category', 'général')}) {m['content']}")
        return "\n".join(lines)

    @classmethod
    def build_system_prompt(cls, context: dict) -> str:
        sections = [cls.SYSTEM_PROMPT_BASE]
        sections.append("\n\n## CONTEXTE DE L'UTILISATEUR\n")
        sections.append(cls._format_profile_section(context.get("profile", {})))
        sections.append("")
        sections.append(cls._format_logs_section(context.get("logs", {})))
        sections.append("")
        sections.append(cls._format_sessions_section(context.get("sessions", {})))
        sections.append("")
        sections.append(cls._format_journals_section(context.get("journals", [])))
        sections.append("")
        sections.append(cls._format_memories_section(context.get("memories", [])))
        sections.append("")
        sections.append(cls._format_objectives_section(
            context.get("active_objectives", []),
            context.get("objective_stats", {}),
        ))
        sections.append("")
        sections.append(cls._format_badges_section(context.get("badges", [])))
        if "relevant_journals" in context:
            sections.append("")
            sections.append(cls._format_journal_hits(context["relevant_journals"]))
        sections.append("\n\n## Conversation\n")
        return "\n".join(sections)

    @classmethod
    def build_insight_prompt(cls, context: dict) -> str:
        system = cls.build_system_prompt(context)
        return f"{system}\n\n{cls.WEEKLY_INSIGHT_PROMPT}"

    @classmethod
    def build_journal_summary_prompt(cls, entries_text: str) -> str:
        return f"{cls.JOURNAL_SUMMARY_PROMPT}\n\n{entries_text}"

    @classmethod
    def build_routine_prompt(cls, context: dict) -> str:
        system = cls.build_system_prompt(context)
        return f"{system}\n\n{cls.ROUTINE_PROMPT}"
