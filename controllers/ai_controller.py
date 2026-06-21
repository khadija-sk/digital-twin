import hashlib
import logging
from datetime import date, timedelta
from typing import Generator

from models.database import get_session
from models.daily_log import DailyLog
from models.study_session import StudySession
from models.objective import Objective

from controllers.llm_controller import LLMController
from services.context_retriever import ContextRetriever
from services.prompt_builder import PromptBuilder
from services.conversation_manager import ConversationManager


class AIController:

    def __init__(self, user_id):
        self.user_id = user_id
        self.retriever = ContextRetriever(user_id)
        self.prompt_builder = PromptBuilder()
        self.conversation = ConversationManager()
        self._llm = LLMController.get_instance()
        self._model_usage = []

    # ── Hash-based load balancing ─────────────────────────

    def _hash_balanced_providers(self, question: str) -> list[tuple]:
        candidates = []
        if self._llm.provider:
            candidates.append((self._llm.provider, "gemini"))
        if self._llm.grok_provider:
            candidates.append((self._llm.grok_provider, "grok"))
        if len(candidates) < 2:
            return candidates
        h = int(hashlib.sha256(question.encode()).hexdigest(), 16)
        idx = h % len(candidates)
        return [candidates[idx], candidates[1 - idx]]

    # ── LLM-powered chat with routing ─────────────────────

    def ask(self, question: str, history: list | None = None) -> str:
        try:
            return self._ask_llm(question, history)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Full LLM ask failed: {e}")

        try:
            return self._simple_llm_call(question)
        except Exception as e:
            logging.getLogger(__name__).warning(f"Simple LLM ask fallback failed: {e}")

        try:
            return self._ask_rule_based(question)
        except Exception as e:
            return f"⚠️ Erreur : {e}"

    def ask_stream(self, question: str, history: list | None = None) -> Generator[str, None, str]:
        last_error = None
        try:
            yield from self._ask_llm_stream(question, history)
            return
        except Exception as e:
            last_error = e
            logging.getLogger(__name__).warning(f"Full LLM stream failed: {e}")

        try:
            yield self._simple_llm_call(question)
            return
        except Exception as e:
            last_error = e
            logging.getLogger(__name__).warning(f"Stream fallback failed: {e}")

        try:
            yield self._ask_rule_based(question)
            return
        except Exception as e:
            last_error = e

        err_msg = str(last_error) if last_error else "Aucune clé API configurée"
        yield f"⚠️ Erreur API : {err_msg[:200]}"

    def _has_context(self) -> bool:
        logs = self._get_logs(7)
        return len(logs) > 0

    def _ask_llm(self, question: str, history: list | None = None) -> str:
        context = self.retriever.get_rag_context(question)
        system_prompt = self.prompt_builder.build_system_prompt(context)

        if history:
            cm = ConversationManager.from_legacy_history(history)
            llm_history = cm.get_history()
        else:
            llm_history = list(self.conversation.get_history())

        context_available = self._has_context()

        tried = set()

        for provider, name in self._hash_balanced_providers(question):
            if provider:
                tried.add(name)
                try:
                    response = provider.chat(system_prompt, question, llm_history)
                    self._llm.log_model_usage(getattr(provider, 'model_name', name), "hash_balanced")
                    self.conversation.add_user_message(question)
                    self.conversation.add_model_message(response)
                    return response
                except Exception:
                    continue

        if self._llm.router:
            try:
                route = self._llm.router.route(question, context_available)
                provider_name, model_name = self._llm.router.get_model_for_route(
                    route,
                    anthropic_available=self._llm.anthropic_provider is not None,
                    gemini_available=self._llm.provider is not None,
                    ollama_available=self._llm.ollama_provider is not None,
                    grok_available=self._llm.grok_provider is not None,
                )
                tried.add(provider_name)
                prov = self._llm._get_provider(provider_name)
                if prov:
                    prov.model_name = model_name
                    response = prov.chat(system_prompt, question, llm_history)
                    self._llm.log_model_usage(model_name, f"chat_{route}")
                    self.conversation.add_user_message(question)
                    self.conversation.add_model_message(response)
                    return response
            except Exception:
                pass

        for provider, name in [
            (self._llm.ollama_provider, "ollama"),
            (self._llm.provider, "gemini"),
            (self._llm.grok_provider, "grok"),
            (self._llm.anthropic_provider, "anthropic"),
        ]:
            if provider and name not in tried:
                try:
                    response = provider.chat(system_prompt, question, llm_history)
                    self._llm.log_model_usage(getattr(provider, 'model_name', name), f"chat_fallback_{name}")
                    self.conversation.add_user_message(question)
                    self.conversation.add_model_message(response)
                    return response
                except Exception:
                    continue

        raise RuntimeError("Aucun fournisseur LLM disponible")

    def _ask_llm_stream(self, question: str, history: list | None = None):
        context = self.retriever.get_rag_context(question)
        system_prompt = self.prompt_builder.build_system_prompt(context)

        if history:
            cm = ConversationManager.from_legacy_history(history)
            llm_history = cm.get_history()
        else:
            llm_history = list(self.conversation.get_history())

        context_available = self._has_context()
        full_response = []
        tried = set()

        for provider, name in self._hash_balanced_providers(question):
            if provider:
                tried.add(name)
                try:
                    for chunk in provider.chat_stream(system_prompt, question, llm_history):
                        full_response.append(chunk)
                        yield chunk
                    self._llm.log_model_usage(getattr(provider, 'model_name', name), "hash_balanced_stream")
                    self.conversation.add_user_message(question)
                    self.conversation.add_model_message("".join(full_response))
                    return
                except Exception:
                    continue

        if self._llm.router:
            try:
                route = self._llm.router.route(question, context_available)
                provider_name, model_name = self._llm.router.get_model_for_route(
                    route,
                    anthropic_available=self._llm.anthropic_provider is not None,
                    gemini_available=self._llm.provider is not None,
                    ollama_available=self._llm.ollama_provider is not None,
                    grok_available=self._llm.grok_provider is not None,
                )
                tried.add(provider_name)
                prov = self._llm._get_provider(provider_name)
                if prov:
                    prov.model_name = model_name
                    for chunk in prov.chat_stream(system_prompt, question, llm_history):
                        full_response.append(chunk)
                        yield chunk
                    self._llm.log_model_usage(model_name, f"chat_stream_{route}")
                    self.conversation.add_user_message(question)
                    self.conversation.add_model_message("".join(full_response))
                    return
            except Exception:
                pass

        for provider, name in [
            (self._llm.ollama_provider, "ollama"),
            (self._llm.provider, "gemini"),
            (self._llm.grok_provider, "grok"),
            (self._llm.anthropic_provider, "anthropic"),
        ]:
            if provider and name not in tried:
                try:
                    for chunk in provider.chat_stream(system_prompt, question, llm_history):
                        full_response.append(chunk)
                        yield chunk
                    full_text = "".join(full_response)
                    self._llm.log_model_usage(getattr(provider, 'model_name', name), f"chat_stream_fallback_{name}")
                    self.conversation.add_user_message(question)
                    self.conversation.add_model_message(full_text)
                    return
                except Exception:
                    continue

        raise RuntimeError("Aucun fournisseur LLM disponible")

    # ── LLM-powered insight ───────────────────────────────

    def get_daily_insight(self) -> str:
        if self._llm and self._llm.is_available:
            try:
                return self._llm_insight()
            except Exception as e:
                logging.getLogger(__name__).exception("Erreur lors de la récupération de l'insight quotidien")
                return self._fallback_insight()
        return self._fallback_insight()

    def _llm_insight(self) -> str:
        context = self.retriever.get_complete_context(7)
        prompt = self.prompt_builder.build_insight_prompt(context)
        self._llm.log_model_usage(self._llm.active_model_name, "insight")
        return self._llm.generate_content(prompt)

    def _fallback_insight(self) -> str:
        logs = self._get_logs(7)
        if not logs:
            return "Commence par faire quelques check-ins pour que je puisse analyser tes tendances ✨"

        scores = [l.score_productivite for l in logs if l.score_productivite is not None]
        insights = []

        if len(scores) >= 2:
            trend = scores[-1] - scores[0]
            if trend >= 15:
                insights.append(f"📈 Score +{trend} pts cette semaine — belle progression !")
            elif trend <= -15:
                insights.append(f"📉 Score -{abs(trend)} pts — essaie de te coucher plus tôt.")

        sleep_vals = [l.sommeil for l in logs]
        avg_sleep = sum(sleep_vals) / len(sleep_vals)
        if avg_sleep < 6:
            insights.append(f"😴 Moyenne {avg_sleep:.1f}h de sommeil — insuffisant, vise 7-8h.")
        elif avg_sleep >= 7.5:
            insights.append(f"💤 Bon sommeil ({avg_sleep:.1f}h) — continue !")

        energy_vals = [l.energie for l in logs]
        if len(energy_vals) >= 3 and energy_vals[-1] < energy_vals[-2] < energy_vals[-3]:
            insights.append("⚠️ Énergie en baisse 3 jours de suite — risque de burnout.")

        mood_vals = [l.humeur for l in logs]
        avg_mood = sum(mood_vals) / len(mood_vals)
        if avg_mood >= 4:
            insights.append(f"😊 Humeur excellente ({avg_mood:.1f}/5) !")
        elif avg_mood <= 2:
            insights.append(f"😕 Humeur basse ({avg_mood:.1f}/5) — prends soin de toi.")

        if not insights:
            avg_score = round(sum(scores) / len(scores)) if scores else 0
            insights.append(f"🧠 Score moyen : {avg_score}/100 sur 7 jours.")

        return "  •  ".join(insights[:2])

    def _simple_llm_call(self, question: str) -> str:
        prompt = "Tu es un assistant IA intelligent et utile. Réponds à toutes les questions en français de façon naturelle et concise."
        for provider, _ in self._hash_balanced_providers(question):
            if provider:
                try:
                    return provider.chat(prompt, question, None)
                except Exception:
                    continue
        for provider, _ in [
            (self._llm.anthropic_provider, "anthropic"),
            (self._llm.ollama_provider, "ollama"),
        ]:
            if provider:
                try:
                    return provider.chat(prompt, question, None)
                except Exception:
                    continue
        raise RuntimeError("Aucun fournisseur LLM disponible")

    # ── Rule-based fallback ──────────────────────────────────

    def _ask_rule_based(self, question: str) -> str:
        q = question.lower()
        logs_7 = self._get_logs(7)
        logs_30 = self._get_logs(30)

        if any(w in q for w in ["burnout", "épuis", "surmen"]):
            return self._analyze_burnout(logs_7)
        if any(w in q for w in ["sommeil", "dormir", "dors", "sleep", "nuit"]):
            return self._analyze_sleep(logs_7)
        if any(w in q for w in ["humeur", "moral", "mood", "bien-être"]):
            return self._analyze_mood(logs_7)
        if any(w in q for w in ["énergie", "energie", "energy"]):
            return self._analyze_energy(logs_7)
        if any(w in q for w in ["score", "productiv", "performance"]):
            return self._analyze_score(logs_7)
        if any(w in q for w in ["pomodoro", "session", "concentration", "focus"]):
            return self._analyze_sessions()
        if any(w in q for w in ["semaine", "bilan", "résumé", "fort", "faible"]):
            return self._weekly_summary(logs_7)
        if any(w in q for w in ["plan", "conseil", "améliorer", "astuce"]):
            return self._build_plan(logs_7)
        if any(w in q for w in ["objectif", "goal", "but"]):
            return self._analyze_objectives()
        if any(w in q for w in ["progress", "tendance", "évolution", "30"]):
            return self._analyze_progress(logs_30)
        if self._llm and self._llm.is_available:
            try:
                return self._simple_llm_call(question)
            except Exception:
                pass
        return self._general_summary(logs_7)

    # ── Data helpers (shared with fallback) ──────────────────

    def _get_logs(self, days=7):
        session = get_session()
        try:
            since = date.today() - timedelta(days=days)
            return session.query(DailyLog).filter(
                DailyLog.utilisateur_id == self.user_id,
                DailyLog.date >= since
            ).order_by(DailyLog.date.asc()).all()
        finally:
            session.close()

    def _get_all_logs(self):
        session = get_session()
        try:
            return session.query(DailyLog).filter_by(utilisateur_id=self.user_id).order_by(DailyLog.date.asc()).all()
        finally:
            session.close()

    def _get_sessions(self):
        session = get_session()
        try:
            return session.query(StudySession).filter_by(utilisateur_id=self.user_id, statut="complete").all()
        finally:
            session.close()

    def _get_objectives(self):
        session = get_session()
        try:
            return session.query(Objective).filter_by(utilisateur_id=self.user_id).all()
        finally:
            session.close()

    # ── Fallback analysis methods (unchanged logic) ──────────

    def _analyze_burnout(self, logs):
        if len(logs) < 3:
            return "Pas assez de données (3 check-ins min). Continue à remplir tes check-ins quotidiens."
        energy = [l.energie for l in logs]
        sleep = [l.sommeil for l in logs]
        mood = [l.humeur for l in logs]
        risk = 0
        details = []
        if len(energy) >= 3 and energy[-1] < energy[-2] < energy[-3]:
            risk += 3
            details.append("énergie en baisse 3 jours consécutifs")
        avg_sleep = sum(sleep) / len(sleep)
        if avg_sleep < 6:
            risk += 2
            details.append(f"sommeil insuffisant ({avg_sleep:.1f}h)")
        avg_mood = sum(mood) / len(mood)
        if avg_mood <= 2:
            risk += 2
            details.append(f"humeur basse ({avg_mood:.1f}/5)")
        if risk >= 5:
            return (f"⚠️ Risque de burnout ÉLEVÉ\n\nSignaux : {', '.join(details)}\n\nActions immédiates :\n• Dors 8h les 3 prochains jours\n• Limite-toi à 2-3 Pomodoros par jour\n• Fais une activité plaisir ce soir\n• Écris dans ton journal ce que tu ressens")
        elif risk >= 2:
            return f"🟡 Fatigue modérée détectée\n\nPoints d'attention : {', '.join(details) if details else 'surveille ton énergie'}\n\nTu n'es pas en burnout, mais ralentis un peu."
        else:
            return "✅ Aucun signe de burnout. Énergie et sommeil semblent stables. Continue !"

    def _analyze_sleep(self, logs):
        if not logs:
            return "Pas encore de données de sommeil. Fais un check-in !"
        vals = [l.sommeil for l in logs]
        avg = sum(vals) / len(vals)
        msg = f"😴 Sommeil — {len(logs)} derniers jours\n\n• Moyenne : {avg:.1f}h / nuit\n• Meilleure nuit : {max(vals)}h\n• Pire nuit : {min(vals)}h\n\n"
        if avg >= 8:    msg += "✅ Excellent ! Tu récupères bien."
        elif avg >= 7:  msg += "👍 Bon sommeil. Vise 8h pour optimiser ton énergie."
        elif avg >= 6:  msg += "⚠️ Insuffisant. Couche-toi 30 min plus tôt chaque soir."
        else:           msg += "🚨 Très court ! Moins de 6h affecte sérieusement ta concentration."
        return msg

    def _analyze_mood(self, logs):
        if not logs:
            return "Pas encore de données d'humeur. Fais un check-in !"
        vals = [l.humeur for l in logs]
        avg = sum(vals) / len(vals)
        msg = f"😊 Humeur — {len(logs)} derniers jours\n\n• Moyenne : {avg:.1f}/5\n• Meilleure journée : {max(vals)}/5\n• Journée difficile : {min(vals)}/5\n\n"
        if avg >= 4:    msg += "✅ Humeur excellente cette semaine !"
        elif avg >= 3:  msg += "👍 Humeur correcte, quelques hauts et bas normaux."
        elif avg >= 2:  msg += "⚠️ Humeur en dessous de la moyenne. Écris dans ton journal."
        else:           msg += "🚨 Humeur très basse. Parle à quelqu'un de confiance."
        return msg

    def _analyze_energy(self, logs):
        if not logs:
            return "Pas encore de données d'énergie. Fais un check-in !"
        vals = [l.energie for l in logs]
        avg = sum(vals) / len(vals)
        trend = ""
        if len(vals) >= 3:
            if vals[-1] > vals[-3]:   trend = "📈 En hausse"
            elif vals[-1] < vals[-3]: trend = "📉 En baisse"
            else:                     trend = "➡️ Stable"
        msg = f"⚡ Énergie — {len(logs)} derniers jours\n\n• Moyenne : {avg:.1f}/5\n• Max : {max(vals)}/5  |  Min : {min(vals)}/5\n"
        if trend: msg += f"• Tendance : {trend}\n\n"
        if avg >= 4:    msg += "✅ Énergie au top !"
        elif avg >= 3:  msg += "👍 Correct. Hydrate-toi et fais des pauses."
        else:           msg += "⚠️ Énergie basse. Vérifie ton sommeil et tes pauses."
        return msg

    def _analyze_score(self, logs):
        if not logs:
            return "Pas encore de scores. Fais ton premier check-in !"
        scores = [l.score_productivite for l in logs if l.score_productivite is not None]
        if not scores:
            return "Scores non disponibles."
        avg = round(sum(scores) / len(scores))
        latest = scores[-1]
        best = max(scores)
        msg = f"🧠 Score de productivité\n\n• Aujourd'hui : {latest}/100\n• Moyenne 7j : {avg}/100\n• Meilleur : {best}/100\n\nFormule : Sommeil (40%) + Humeur (30%) + Énergie (30%)\n\n"
        if avg >= 75:   msg += "✅ Excellent niveau !"
        elif avg >= 55: msg += "👍 Bon niveau. Améliore ton sommeil en priorité (+40%)."
        elif avg >= 35: msg += "⚠️ Score moyen. Focus sur le sommeil d'abord."
        else:           msg += "🚨 Score bas. Dors 8h ce soir — impact direct de 40%."
        return msg

    def _analyze_sessions(self):
        sessions = self._get_sessions()
        total = len(sessions)
        if total == 0:
            return "Aucune session Pomodoro complétée. Lance ton premier timer !"
        week_ago = date.today() - timedelta(days=7)
        this_week = [s for s in sessions if s.date_heure_debut.date() >= week_ago]
        msg = f"🍅 Sessions Pomodoro\n\n• Total : {total} sessions\n• Cette semaine : {len(this_week)} sessions\n• Temps total : ~{total * 25} min ({round(total * 25 / 60, 1)}h)\n\n"
        if len(this_week) >= 10:  msg += "🔥 Semaine très productive ! Récupère le week-end."
        elif len(this_week) >= 5: msg += "✅ Bonne cadence de travail."
        elif len(this_week) >= 1: msg += "👍 Tu travailles. Vise 3-5 sessions/jour."
        else:                     msg += "⚠️ Aucune session cette semaine. Lance-toi maintenant !"
        return msg

    def _weekly_summary(self, logs):
        if not logs:
            return "Pas assez de données. Fais quelques check-ins d'abord !"
        scores = [l.score_productivite for l in logs if l.score_productivite is not None]
        sleeps = [l.sommeil for l in logs]
        moods = [l.humeur for l in logs]
        energys = [l.energie for l in logs]
        avg_score = round(sum(scores) / len(scores)) if scores else 0
        avg_sleep = round(sum(sleeps) / len(sleeps), 1)
        avg_mood = round(sum(moods) / len(moods), 1)
        avg_energy = round(sum(energys) / len(energys), 1)
        strengths, improvements = [], []
        if avg_sleep >= 7.5: strengths.append(f"sommeil ({avg_sleep}h)")
        else:                  improvements.append(f"sommeil ({avg_sleep}h)")
        if avg_mood >= 3.5: strengths.append(f"humeur ({avg_mood}/5)")
        else:                  improvements.append(f"humeur ({avg_mood}/5)")
        if avg_energy >= 3.5: strengths.append(f"énergie ({avg_energy}/5)")
        else:                  improvements.append(f"énergie ({avg_energy}/5)")
        msg = f"📊 Bilan semaine ({len(logs)} check-ins)\n\nScore moyen : {avg_score}/100\n\n"
        if strengths:    msg += f"✅ Points forts : {', '.join(strengths)}\n"
        if improvements: msg += f"⚠️ À améliorer : {', '.join(improvements)}\n"
        return msg

    def _build_plan(self, logs):
        if not logs:
            return "Fais d'abord quelques check-ins pour un plan personnalisé !"
        avg_sleep = sum(l.sommeil for l in logs) / len(logs)
        avg_mood = sum(l.humeur for l in logs) / len(logs)
        avg_energy = sum(l.energie for l in logs) / len(logs)
        plan = "📋 Plan personnalisé\n\n"
        n = 1
        if avg_sleep < 7:
            plan += f"{n}. 🛌 SOMMEIL : couche-toi 30 min plus tôt. Vise 7-8h.\n"; n += 1
        if avg_energy < 3:
            plan += f"{n}. ⚡ ÉNERGIE : pause de 10 min toutes les heures. Hydrate-toi.\n"; n += 1
        if avg_mood < 3:
            plan += f"{n}. 😊 HUMEUR : 30 min/jour pour une activité plaisir.\n"; n += 1
        plan += f"{n}. 🍅 POMODORO : 4 sessions de 25 min par jour.\n"; n += 1
        plan += f"{n}. 📓 JOURNAL : écris chaque soir avant de dormir.\n"
        return plan

    def _analyze_objectives(self):
        objectives = self._get_objectives()
        if not objectives:
            return "Aucun objectif créé. Va dans 'Objectifs' pour en ajouter !"
        active = [o for o in objectives if o.statut == "actif"]
        achieved = [o for o in objectives if o.statut == "atteint"]
        msg = f"🎯 Objectifs\n\n• Actifs : {len(active)}  |  Atteints : {len(achieved)}\n\n"
        if active:
            msg += "En cours :\n"
            for o in active[:5]:
                msg += f"  → {o.description}\n"
        if achieved:
            msg += f"\n✅ Bravo ! {len(achieved)} objectif(s) atteint(s)."
        return msg

    def _analyze_progress(self, logs):
        if len(logs) < 7:
            return f"Seulement {len(logs)} check-in(s). Continue pour voir ta progression sur 30 jours !"
        scores = [l.score_productivite for l in logs if l.score_productivite is not None]
        if not scores:
            return "Pas encore de scores calculés."
        first = scores[:min(7, len(scores)//2)]
        last = scores[-(min(7, len(scores)//2)):]
        avg_first = round(sum(first) / len(first))
        avg_last = round(sum(last) / len(last))
        delta = avg_last - avg_first
        msg = f"📈 Progression ({len(logs)} jours)\n\n• Score début : {avg_first}/100\n• Score récent : {avg_last}/100\n• Évolution : {'+' if delta >= 0 else ''}{delta} points\n\n"
        if delta >= 10:   msg += "🚀 Progression remarquable !"
        elif delta >= 0:  msg += "✅ Légère progression. Continue !"
        elif delta >= -10:msg += "⚠️ Légère baisse. Revois tes habitudes."
        else:             msg += "🚨 Baisse significative. Analyse ce qui a changé."
        return msg

    def _general_summary(self, logs):
        score = round(sum(l.score_productivite for l in logs if l.score_productivite is not None) / max(len([l for l in logs if l.score_productivite is not None]), 1))
        return (
            f"Je suis ton assistant IA Digital Twin. Je peux répondre à toutes tes questions — "
            f"sur tes données de productivité (score moyen : {score}/100), "
            f"ou sur n'importe quel sujet général (science, technologie, culture, conseils...). "
            f"Pose-moi tout ce qui te passe par la tête !"
        )

    @staticmethod
    def suggested_questions():
        return [
            "Quels sont mes points forts cette semaine ?",
            "Explique-moi le machine learning simplement",
            "Donne-moi un plan pour cette semaine",
            "Qu'est-ce que la théorie de la relativité ?",
            "Comment améliorer mon sommeil ?",
            "Écris un poème sur la productivité",
            "Donne-moi des conseils pour apprendre Python",
            "Analyse mon niveau d'énergie",
        ]
