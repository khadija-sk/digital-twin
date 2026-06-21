import os
import platform
import urllib.request
import urllib.error
from datetime import date
from typing import Optional

from fpdf import FPDF

_FONT_CACHE = os.path.join(os.path.dirname(__file__), "..", "fonts")

# fpdf2 set_font(family, style, size) resolves the font key as family.lower() + style.lower().
# We register each variant with its style so the lookup matches:
#   add_font("Sans", "", ...)  → key "sans"
#   add_font("Sans", "B", ...) → key "sansb"
#   add_font("Sans", "I", ...) → key "sansi"
_FONT_CANDIDATES = [
    (lambda: _FONT_CACHE, [
        ("DejaVuSans.ttf", "DejaVu", ""),
        ("DejaVuSans-Bold.ttf", "DejaVu", "B"),
        ("DejaVuSans-Oblique.ttf", "DejaVu", "I"),
    ]),
    ("system", [
        ("DejaVuSans.ttf", "DejaVu", ""),
        ("DejaVuSans-Bold.ttf", "DejaVu", "B"),
        ("DejaVuSans-Oblique.ttf", "DejaVu", "I"),
    ]),
    ("system", [
        ("arial.ttf", "Sans", ""),
        ("arialbd.ttf", "Sans", "B"),
        ("ariali.ttf", "Sans", "I"),
    ]),
]


def _find_system_font_dir() -> str:
    system = platform.system()
    if system == "Windows":
        return os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts")
    elif system == "Darwin":
        return "/System/Library/Fonts"
    else:
        return "/usr/share/fonts/truetype/dejavu"


def _resolve_candidate_dir(label: str) -> str:
    if label == "system":
        return _find_system_font_dir()
    return os.path.abspath(label())


def _find_fonts() -> list[tuple[str, str, str]]:
    for label, variants in _FONT_CANDIDATES:
        directory = _resolve_candidate_dir(label)
        if label == "system":
            pass  # don't create system dirs
        elif isinstance(label, str):
            pass
        else:
            try:
                os.makedirs(directory, exist_ok=True)
            except (OSError, PermissionError):
                pass
        found = [(fn, fam, sty) for fn, fam, sty in variants
                 if os.path.exists(os.path.join(directory, fn))]
        if len(found) == len(variants):
            return [(fam, sty, os.path.join(directory, fn)) for fn, fam, sty in variants]
    return []


def _download_dejavu():
    dest = os.path.abspath(_FONT_CACHE)
    try:
        os.makedirs(dest, exist_ok=True)
    except (OSError, PermissionError):
        return
    base = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/"
    for name in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVuSans-Oblique.ttf"):
        url = base + name
        out = os.path.join(dest, name)
        if not os.path.exists(out):
            try:
                urllib.request.urlretrieve(url, out)
            except (urllib.error.URLError, OSError):
                return
    global _FONT_VARIANTS
    _FONT_VARIANTS = _find_fonts()


_FONT_VARIANTS = _find_fonts()
if not _FONT_VARIANTS:
    _download_dejavu()
    _FONT_VARIANTS = _find_fonts()

if _FONT_VARIANTS:
    _FONT_NAME = _FONT_VARIANTS[0][0]
    _FONT_BOLD = _FONT_NAME
    _FONT_ITALIC = _FONT_NAME

    def _init_fonts(pdf: FPDF):
        for family, style, path in _FONT_VARIANTS:
            pdf.add_font(family, style, path, uni=True)
else:
    _FONT_NAME = "Courier"
    _FONT_BOLD = "Courier"
    _FONT_ITALIC = "Courier"

    def _init_fonts(pdf: FPDF):
        pass


class PDFExporter:

    @staticmethod
    def _new_doc() -> FPDF:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.alias_nb_pages()
        pdf.add_page()
        _init_fonts(pdf)
        return pdf

    @staticmethod
    def _header(pdf: FPDF, title: str, subtitle: str = ""):
        pdf.set_font(_FONT_NAME, "B", 16)
        pdf.set_text_color(30, 7, 8)
        pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        if subtitle:
            pdf.set_font(_FONT_NAME, "", 9)
            pdf.set_text_color(136, 75, 67)
            pdf.cell(0, 6, subtitle, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.set_draw_color(180, 160, 150)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

    @staticmethod
    def _sub_heading(pdf: FPDF, text: str):
        pdf.set_font(_FONT_NAME, "B", 11)
        pdf.set_text_color(30, 7, 8)
        pdf.cell(0, 9, text, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

    @staticmethod
    def _body(pdf: FPDF, text: str):
        pdf.set_font(_FONT_NAME, "", 9)
        pdf.set_text_color(30, 7, 8)
        pdf.multi_cell(0, 5, text)
        pdf.ln(2)

    @staticmethod
    def _table(pdf: FPDF, headers: list[str], rows: list[list[str]], col_widths: Optional[list[int]] = None):
        if col_widths is None:
            col_widths = [190 // len(headers)] * len(headers)
        pdf.set_font(_FONT_NAME, "B", 8)
        pdf.set_fill_color(30, 7, 8)
        pdf.set_text_color(247, 244, 213)
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 7, header, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_font(_FONT_NAME, "", 8)
        pdf.set_text_color(30, 7, 8)
        for row_idx, row in enumerate(rows):
            if row_idx % 2 == 0:
                pdf.set_fill_color(247, 244, 213)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(220, 220, 220)
            max_lines = 1
            cell_texts = []
            for i, cell in enumerate(row):
                lines = pdf.multi_cell(col_widths[i], 4.5, str(cell), dry_run=True, output="LINES")
                max_lines = max(max_lines, len(lines))
                cell_texts.append(str(cell))
            row_h = max_lines * 4.5
            for i, cell_text in enumerate(cell_texts):
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.rect(x, y, col_widths[i], row_h)
                pdf.set_xy(x + 0.5, y + 0.5)
                pdf.multi_cell(col_widths[i] - 1, 4.5, cell_text, border=0)
                pdf.set_xy(x + col_widths[i], y)
            pdf.ln(row_h)

    @staticmethod
    def _check_page_break(pdf: FPDF, needed: float):
        if pdf.get_y() + needed > 270:
            pdf.add_page()

    # ─── PUBLIC EXPORT METHODS ─────────────────────────────────

    @staticmethod
    def export_checkins(logs, path: str, user_name: str = ""):
        pdf = PDFExporter._new_doc()
        title = "Rapport des check-ins"
        sub = f"Utilisateur : {user_name}" if user_name else ""
        PDFExporter._header(pdf, title, sub)
        if not logs:
            pdf.cell(0, 10, "Aucune donnee de check-in.", align="C")
            pdf.output(path)
            return
        stats = (
            f"Periode : du {logs[0].date} au {logs[-1].date}  |  "
            f"Total : {len(logs)} check-ins"
        )
        PDFExporter._body(pdf, stats)
        headers = ["Date", "Humeur", "Energie", "Sommeil", "Score"]
        widths  = [45, 35, 35, 35, 40]
        rows = []
        scores = []
        for log in logs:
            rows.append([
                str(log.date), f"{log.humeur}/5", f"{log.energie}/5",
                f"{log.sommeil}h", str(log.score_productivite or "-")
            ])
            if log.score_productivite:
                scores.append(log.score_productivite)
        PDFExporter._table(pdf, headers, rows, widths)
        if scores:
            avg = sum(scores) / len(scores)
            pdf.ln(4)
            pdf.set_font(_FONT_NAME, "I", 9)
            pdf.set_text_color(136, 75, 67)
            pdf.cell(0, 6, f"Score moyen : {avg:.1f}/100", align="R")
        pdf.output(path)

    @staticmethod
    def export_sessions(sessions, path: str, user_name: str = ""):
        pdf = PDFExporter._new_doc()
        title = "Rapport des sessions Pomodoro"
        sub = f"Utilisateur : {user_name}" if user_name else ""
        PDFExporter._header(pdf, title, sub)
        if not sessions:
            pdf.cell(0, 10, "Aucune session Pomodoro.", align="C")
            pdf.output(path)
            return
        complete = [s for s in sessions if s.statut == "complete"]
        stats = (
            f"Total : {len(sessions)} sessions  |  "
            f"Completees : {len(complete)}  |  "
            f"Temps total : {len(complete) * 25} min (~{len(complete) * 25 // 60}h)"
        )
        PDFExporter._body(pdf, stats)
        headers = ["Date/Heure", "Duree", "Statut", "Energie"]
        widths  = [60, 40, 45, 45]
        rows = []
        for s in sessions:
            status = "Completee" if s.statut == "complete" else "Abandonnee"
            rows.append([
                str(s.date_heure_debut)[:16],
                f"{s.duree} min",
                status,
                f"{s.energie_mi_session}/5" if s.energie_mi_session else "-",
            ])
        PDFExporter._table(pdf, headers, rows, widths)
        pdf.output(path)

    @staticmethod
    def export_journal(entries, path: str, user_name: str = ""):
        pdf = PDFExporter._new_doc()
        title = "Journal personnel"
        sub = f"Utilisateur : {user_name}" if user_name else ""
        PDFExporter._header(pdf, title, sub)
        if not entries:
            pdf.cell(0, 10, "Aucune entree de journal.", align="C")
            pdf.output(path)
            return
        pdf.cell(0, 6, f"{len(entries)} entree(s) du journal", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)
        for entry in entries:
            PDFExporter._check_page_break(pdf, 30)
            pdf.set_font(_FONT_NAME, "B", 11)
            pdf.set_text_color(136, 75, 67)
            pdf.cell(0, 7, f"  {entry.date}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(_FONT_NAME, "", 10)
            pdf.set_text_color(30, 7, 8)
            pdf.set_x(14)
            pdf.multi_cell(182, 5.5, entry.contenu)
            pdf.ln(3)
            pdf.set_draw_color(230, 230, 230)
            pdf.line(14, pdf.get_y(), 196, pdf.get_y())
            pdf.ln(3)
        pdf.output(path)

    @staticmethod
    def export_goals(goals, path: str, user_name: str = ""):
        pdf = PDFExporter._new_doc()
        title = "Objectifs"
        sub = f"Utilisateur : {user_name}" if user_name else ""
        PDFExporter._header(pdf, title, sub)
        if not goals:
            pdf.cell(0, 10, "Aucun objectif defini.", align="C")
            pdf.output(path)
            return
        active = [g for g in goals if g.statut == "actif"]
        achieved = [g for g in goals if g.statut == "atteint"]
        stats = f"Actifs : {len(active)}  |  Atteints : {len(achieved)}  |  Total : {len(goals)}"
        PDFExporter._body(pdf, stats)
        headers = ["Description", "Cible", "Statut", "Cree le"]
        widths  = [70, 35, 45, 40]
        rows = []
        for g in goals:
            status = "Atteint" if g.statut == "atteint" else "Actif"
            rows.append([
                g.description,
                f"{g.valeur_cible} {g.unite or ''}".strip(),
                status,
                str(g.date_creation),
            ])
        PDFExporter._table(pdf, headers, rows, widths)
        pdf.output(path)

    @staticmethod
    def export_badges(badges, path: str, user_name: str = ""):
        pdf = PDFExporter._new_doc()
        title = "Badges debloques"
        sub = f"Utilisateur : {user_name}" if user_name else ""
        PDFExporter._header(pdf, title, sub)
        if not badges:
            pdf.cell(0, 10, "Aucun badge debloque.", align="C")
            pdf.output(path)
            return
        total_xp = sum(b.xp_gagne for b in badges)
        stats = f"Total : {len(badges)} badges  |  XP total gagne : {total_xp}"
        PDFExporter._body(pdf, stats)
        headers = ["Icone", "Nom", "Description", "Date", "XP"]
        widths  = [20, 50, 65, 30, 25]
        rows = []
        for b in badges:
            icon = b.icone or "*"
            rows.append([
                icon, b.nom, b.description or "",
                str(b.date_obtention), str(b.xp_gagne),
            ])
        PDFExporter._table(pdf, headers, rows, widths)
        pdf.output(path)

    @staticmethod
    def export_chat_history(history: list[dict], path: str, user_name: str = ""):
        pdf = PDFExporter._new_doc()
        title = "Conversation IA"
        sub = f"Utilisateur : {user_name}" if user_name else ""
        PDFExporter._header(pdf, title, sub)
        if not history:
            pdf.cell(0, 10, "Aucune conversation.", align="C")
            pdf.output(path)
            return
        messages = len([m for m in history if m.get("role") in ("user", "assistant")])
        pdf.cell(0, 6, f"{messages} message(s)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(6)
        display_name = user_name or "Utilisateur"
        for msg in history:
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue
            PDFExporter._check_page_break(pdf, 25)
            is_user = role == "user"
            content = msg.get("content", "") or ""
            if isinstance(content, list):
                content = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
            label = f"  {display_name if is_user else 'Assistant'}  "
            pdf.set_font(_FONT_NAME, "B", 10)
            if is_user:
                pdf.set_text_color(136, 75, 67)
            else:
                pdf.set_text_color(131, 153, 88)
            pdf.cell(0, 7, label, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font(_FONT_NAME, "", 10)
            pdf.set_text_color(30, 7, 8)
            pdf.set_x(14)
            pdf.multi_cell(182, 5.5, content)
            pdf.ln(2)
            pdf.set_draw_color(240, 240, 240)
            pdf.line(14, pdf.get_y(), 196, pdf.get_y())
            pdf.ln(2)
        pdf.output(path)

    @staticmethod
    def export_analytics(
        path: str, user_name: str = "",
        score_series: Optional[list] = None,
        sleep_series: Optional[list] = None,
        mood_series: Optional[list] = None,
        energy_series: Optional[list] = None,
        avg_score: float = 0,
        avg_sleep: float = 0,
        avg_mood: float = 0,
        avg_energy: float = 0,
        streak: int = 0,
        total_checkins: int = 0,
        total_sessions: int = 0,
        period_days: int = 7,
    ):
        pdf = PDFExporter._new_doc()
        title = "Rapport d'analytiques"
        sub = f"Utilisateur : {user_name}" if user_name else ""
        PDFExporter._header(pdf, title, sub)

        pdf.set_font(_FONT_NAME, "B", 13)
        pdf.set_text_color(30, 7, 8)
        pdf.cell(0, 10, f"Vue d'ensemble ({period_days} jours)", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

        metrics = [
            ("Score moyen", f"{avg_score}/100"),
            ("Sommeil moyen", f"{avg_sleep}h"),
            ("Humeur moyenne", f"{avg_mood}/5"),
            ("Energie moyenne", f"{avg_energy}/5"),
            ("Serie actuelle", f"{streak} jours"),
            ("Check-ins", str(total_checkins)),
            ("Sessions Pomodoro", str(total_sessions)),
        ]
        col_w = 60
        pdf.set_font(_FONT_NAME, "", 10)
        for i, (label, value) in enumerate(metrics):
            if i % 3 == 0 and i > 0:
                pdf.ln()
            x_start = 10 + (i % 3) * col_w
            pdf.set_xy(x_start, pdf.get_y())
            pdf.set_font(_FONT_NAME, "B", 9)
            pdf.set_text_color(136, 75, 67)
            pdf.cell(col_w - 4, 6, label)
            pdf.set_xy(x_start, pdf.get_y() + 6)
            pdf.set_font(_FONT_NAME, "", 12)
            pdf.set_text_color(30, 7, 8)
            pdf.cell(col_w - 4, 8, value)
        pdf.ln(20)

        if score_series:
            PDFExporter._check_page_break(pdf, 20)
            PDFExporter._sub_heading(pdf, "Evolution du score")
            headers = ["Date", "Score", "Sommeil", "Humeur", "Energie"]
            widths  = [40, 35, 35, 35, 35]
            rows = []
            for s in score_series:
                rows.append([
                    s.get("date", ""), str(s.get("score", "")),
                    str(s.get("sleep", "")), str(s.get("mood", "")),
                    str(s.get("energy", "")),
                ])
            PDFExporter._table(pdf, headers, rows, widths)

        pdf.output(path)

    @staticmethod
    def export_report(
        path: str, user_name: str = "",
        checkins: Optional[list] = None,
        sessions: Optional[list] = None,
        journals: Optional[list] = None,
        goals: Optional[list] = None,
        badges: Optional[list] = None,
    ):
        pdf = PDFExporter._new_doc()
        title = "Rapport complet Digital Twin"
        sub = f"Utilisateur : {user_name}  |  Genere le {date.today()}"
        PDFExporter._header(pdf, title, sub)

        pdf.set_font(_FONT_NAME, "", 10)
        pdf.set_text_color(30, 7, 8)
        pdf.multi_cell(0, 5.5, (
            "Ce rapport regroupe l'ensemble de vos donnees personnelles "
            "suivies dans Digital Twin : check-ins, sessions Pomodoro, "
            "entrees de journal, objectifs et badges."
        ))
        pdf.ln(6)

        sections = []

        if checkins:
            sections.append(("Check-ins", checkins))
        if sessions:
            sections.append(("Sessions Pomodoro", sessions))
        if journals:
            sections.append(("Journal", journals))
        if goals:
            sections.append(("Objectifs", goals))
        if badges:
            sections.append(("Badges", badges))

        for section_name, data in sections:
            PDFExporter._check_page_break(pdf, 30)
            pdf.set_font(_FONT_NAME, "B", 14)
            pdf.set_text_color(30, 7, 8)
            pdf.cell(0, 10, section_name, new_x="LMARGIN", new_y="NEXT")
            pdf.set_draw_color(180, 160, 150)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
            pdf.set_font(_FONT_NAME, "", 10)
            pdf.set_text_color(136, 75, 67)
            pdf.cell(0, 6, f"{len(data)} entree(s)", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
            for item in data[:50]:
                PDFExporter._check_page_break(pdf, 8)
                pdf.set_font(_FONT_NAME, "", 9)
                pdf.set_text_color(30, 7, 8)
                pdf.set_x(14)
                short = str(item)[:120]
                pdf.multi_cell(182, 5, f"  {short}")
                pdf.ln(1)
            if len(data) > 50:
                pdf.set_font(_FONT_NAME, "I", 9)
                pdf.set_text_color(150, 150, 150)
                pdf.cell(0, 6, f"... et {len(data) - 50} entree(s) supplementaires", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(4)

        pdf.output(path)
