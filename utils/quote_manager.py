# utils/quote_manager.py

import random

QUOTES = {
    "high_energy": [
        ("L'action est la clé fondamentale de tout succès.", "Pablo Picasso"),
        ("Le secret du succès, c'est de commencer.", "Mark Twain"),
        ("Chaque expert a d'abord été un débutant.", "Helen Hayes"),
        ("La discipline est le pont entre les objectifs et les accomplissements.", "Jim Rohn"),
        ("Fais aujourd'hui ce que les autres ne veulent pas faire.", "Anonymous"),
    ],
    "low_energy": [
        ("Prends soin de ton corps. C'est le seul endroit où tu dois vivre.", "Jim Rohn"),
        ("Le repos n'est pas de la paresse.", "John Lubbock"),
        ("Même un petit pas en avant est un progrès.", "Anonymous"),
        ("Tu n'as pas à aller vite. Tu dois juste continuer.", "Anonymous"),
        ("Les grandes choses ne sont pas faites par une impulsion.", "Vincent Van Gogh"),
    ],
    "low_mood": [
        ("Après la pluie, le beau temps.", "Proverbe"),
        ("Tu es plus fort·e que tu ne le crois.", "A.A. Milne"),
        ("Cette émotion aussi passera.", "Anonymous"),
        ("Prends soin de toi d'abord.", "Anonymous"),
        ("Chaque journée est une nouvelle chance.", "Anonymous"),
    ],
    "high_mood": [
        ("Le bonheur n'est pas quelque chose de prêt à l'emploi.", "Dalaï Lama"),
        ("Vis dans l'instant présent.", "Anonymous"),
        ("Rayonne ta lumière.", "Anonymous"),
        ("L'enthousiasme est le moteur du succès.", "Ralph Waldo Emerson"),
        ("Aujourd'hui est un excellent jour.", "Anonymous"),
    ],
    "default": [
        ("Petit à petit, l'oiseau fait son nid.", "Proverbe"),
        ("La constance est la vertu des forts.", "Anonymous"),
        ("Commence là où tu es. Utilise ce que tu as.", "Arthur Ashe"),
        ("Un voyage de mille lieues commence par un pas.", "Lao-Tseu"),
        ("Le succès n'est pas final, l'échec n'est pas fatal.", "Winston Churchill"),
    ]
}

class QuoteManager:

    @staticmethod
    def get_quote(humeur: int = 3, energie: int = 3) -> dict:
        if energie >= 4:
            pool = QUOTES["high_energy"]
        elif energie <= 2:
            pool = QUOTES["low_energy"]
        elif humeur <= 2:
            pool = QUOTES["low_mood"]
        elif humeur >= 4:
            pool = QUOTES["high_mood"]
        else:
            pool = QUOTES["default"]
        text, author = random.choice(pool)
        return {"text": text, "author": author}

    @staticmethod
    def get_random_quote() -> dict:
        all_quotes = [q for pool in QUOTES.values() for q in pool]
        text, author = random.choice(all_quotes)
        return {"text": text, "author": author}