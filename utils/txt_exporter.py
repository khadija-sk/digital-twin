from datetime import date


class TXTExporter:

    @staticmethod
    def _separator(title="") -> str:
        line = "=" * 60
        if title:
            return f"\n{line}\n{title.upper()}\n{line}\n"
        return f"\n{line}\n"

    @staticmethod
    def export_checkins(logs, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Rapport des check-ins\n")
            f.write(f"Généré le {date.today()}\n")
            f.write(TXTExporter._separator())
            if not logs:
                f.write("Aucune donnée de check-in.\n")
                return
            headers = ["Date", "Sommeil", "Humeur", "Énergie", "Score", "Notes"]
            f.write(" | ".join(headers) + "\n")
            f.write("-" * 60 + "\n")
            for log in logs:
                notes = (getattr(log, "notes", "") or "")[:50]
                f.write(f"{log.date} | {getattr(log, 'sommeil', '-')}h | "
                        f"{getattr(log, 'humeur', '-')}/5 | {getattr(log, 'energie', '-')}/5 | "
                        f"{getattr(log, 'score_productivite', '-')} | {notes}\n")

    @staticmethod
    def export_journal(entries, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Journal intime\n")
            f.write(f"Généré le {date.today()}\n")
            f.write(TXTExporter._separator())
            if not entries:
                f.write("Aucune entrée de journal.\n")
                return
            for entry in entries:
                f.write(f"\n[{entry.date}] - Humeur: {getattr(entry, 'humeur', '-')}/5\n")
                f.write(f"{getattr(entry, 'contenu', '(vide)')}\n")
                f.write("-" * 40 + "\n")

    @staticmethod
    def export_analytics(data: dict, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Analytiques\n")
            f.write(f"Généré le {date.today()}\n")
            f.write(TXTExporter._separator())
            for key, value in data.items():
                f.write(f"{key}: {value}\n")

    @staticmethod
    def export_chat_history(messages: list, path: str):
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Historique de conversation IA\n")
            f.write(f"Généré le {date.today()}\n")
            f.write(TXTExporter._separator())
            if not messages:
                f.write("Aucun message.\n")
                return
            for msg in messages:
                role = msg.get("role", "inconnu").upper()
                content = msg.get("parts", [{}])[0].get("text", "") if isinstance(msg.get("parts"), list) else str(msg.get("parts", ""))
                f.write(f"\n[{role}]\n{content}\n")
