# utils/sound_manager.py

import logging

class SoundManager:
    _enabled = True

    @classmethod
    def set_enabled(cls, enabled: bool):
        cls._enabled = enabled

    @classmethod
    def play_start(cls):
        cls._beep(frequency=880, duration=150)

    @classmethod
    def play_done(cls):
        cls._beep(frequency=660, duration=200)
        cls._beep(frequency=880, duration=300)

    @classmethod
    def play_break_done(cls):
        cls._beep(frequency=440, duration=250)

    @classmethod
    def _beep(cls, frequency=880, duration=200):
        if not cls._enabled:
            return
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            import numpy as np
            sample_rate = 44100
            frames = int(sample_rate * duration / 1000)
            t = np.linspace(0, duration / 1000, frames, endpoint=False)
            wave = (np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(wave)
            sound.play()
            pygame.time.wait(duration)
        except Exception as e:
            logging.getLogger(__name__).warning("Erreur lors de la lecture du son")