import logging

logger = logging.getLogger(__name__)

try:
    from PySide6.QtTextToSpeech import QTextToSpeech
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

try:
    import speech_recognition as sr
    import sounddevice as sd
    import numpy as np
    HAS_STT = True
except ImportError:
    HAS_STT = False


class VoiceService:

    def __init__(self):
        self._tts = None
        if HAS_TTS:
            try:
                self._tts = QTextToSpeech()
            except Exception as e:
                logger.warning(f"Failed to init TTS: {e}")
        self._recognizer = sr.Recognizer() if HAS_STT else None
        self._mic = None
        self._listening = False

    def speak(self, text: str):
        if self._tts:
            try:
                self._tts.say(text)
                return True
            except Exception as e:
                logger.warning(f"TTS failed: {e}")
        return False

    def stop_speaking(self):
        if self._tts:
            try:
                self._tts.stop()
            except Exception:
                pass

    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> str:
        if not HAS_STT or not self._recognizer:
            return ""

        try:
            return self._listen_sounddevice(timeout, phrase_time_limit)
        except Exception as e:
            logger.warning(f"sounddevice failed, falling back to sr.Microphone: {e}")
            try:
                return self._listen_microphone(timeout, phrase_time_limit)
            except Exception as e2:
                logger.warning(f"Microphone fallback also failed: {e2}")
                return ""

    def _listen_microphone(self, timeout: int, phrase_time_limit: int) -> str:
        if self._mic is None:
            self._mic = sr.Microphone()
        with self._mic as source:
            self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = self._recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_time_limit
            )
        return self._recognizer.recognize_google(audio, language="fr-FR")

    def _listen_sounddevice(self, timeout: int, phrase_time_limit: int) -> str:
        samplerate = 16000
        duration = min(timeout + phrase_time_limit, 15)
        recording = sd.rec(
            int(samplerate * duration),
            samplerate=samplerate,
            channels=1,
            dtype="int16",
            blocking=True,
        )
        # VAD: skip silent audio (simple RMS threshold)
        rms = np.sqrt(np.mean(recording.astype(np.float32) ** 2))
        if rms < 100:
            return ""
        audio_data = sr.AudioData(
            recording.tobytes(), samplerate, sample_width=2
        )
        return self._recognizer.recognize_google(audio_data, language="fr-FR")

    @property
    def tts_available(self) -> bool:
        return self._tts is not None

    @property
    def stt_available(self) -> bool:
        return HAS_STT and self._recognizer is not None
