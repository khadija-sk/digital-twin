import csv


class CSVExporter:
    BOM = "\ufeff"

    @staticmethod
    def _write(path: str, headers: list[str], rows: list[list]):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            f.write(CSVExporter.BOM)
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)

    @staticmethod
    def export_checkins(logs, path: str):
        rows = []
        for log in logs:
            rows.append([
                str(log.date), log.humeur, log.energie,
                log.sommeil, log.score_productivite or ""
            ])
        CSVExporter._write(
            path,
            ["Date", "Humeur", "Énergie", "Sommeil (h)", "Score Productivité"],
            rows,
        )

    @staticmethod
    def export_sessions(sessions, path: str):
        rows = []
        for s in sessions:
            rows.append([
                str(s.date_heure_debut), s.duree, s.statut,
                s.energie_mi_session if s.energie_mi_session else ""
            ])
        CSVExporter._write(
            path,
            ["Date/Heure", "Durée (min)", "Statut", "Énergie mi-session"],
            rows,
        )

    @staticmethod
    def export_journal(entries, path: str):
        rows = []
        for e in entries:
            rows.append([str(e.date), e.contenu])
        CSVExporter._write(path, ["Date", "Contenu"], rows)

    @staticmethod
    def export_goals(goals, path: str):
        rows = []
        for g in goals:
            rows.append([
                g.description, str(g.valeur_cible),
                g.unite or "", str(g.date_creation), g.statut
            ])
        CSVExporter._write(
            path,
            ["Description", "Valeur cible", "Unité", "Date création", "Statut"],
            rows,
        )

    @staticmethod
    def export_badges(badges, path: str):
        rows = []
        for b in badges:
            rows.append([
                b.icone or "", b.nom, b.description or "",
                str(b.date_obtention), str(b.xp_gagne)
            ])
        CSVExporter._write(
            path,
            ["Icône", "Nom", "Description", "Date obtention", "XP gagné"],
            rows,
        )
