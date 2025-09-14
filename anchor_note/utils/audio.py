"""
audio.py

Small wrapper around pygame.mixer to:
- play a sound once
- run a repeating alert: play continuously for 'burst_seconds', stop, sleep repeat_interval_seconds, repeat until stopped
"""

import threading
import time
import os
import logging
import pygame

LOG = logging.getLogger(__name__)

# Initialize mixer lazily
def _ensure_mixer():
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
    except Exception:
        try:
            pygame.init()
            pygame.mixer.init()
        except Exception:
            LOG.exception("pygame mixer init failed")

def play_once(sound_path: str):
    """Play a single sound once (non-blocking)."""
    if not sound_path or not os.path.exists(sound_path):
        LOG.warning("play_once: sound file not found: %s", sound_path)
        return
    try:
        _ensure_mixer()
        s = pygame.mixer.Sound(sound_path)
        s.play()
    except Exception:
        LOG.exception("play_once failed")

class RepeatingAlert:
    def __init__(self, sound_file: str, burst_seconds: int = 30, repeat_interval_seconds: int = 120):
        self.sound_file = sound_file
        self.burst_seconds = int(burst_seconds)
        self.repeat_interval_seconds = int(repeat_interval_seconds)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        # preload sound if possible
        try:
            _ensure_mixer()
            if sound_file and os.path.exists(sound_file):
                self._sound = pygame.mixer.Sound(sound_file)
            else:
                self._sound = None
        except Exception:
            self._sound = None

    def start(self):
        if not self._thread.is_alive():
            self._stop.clear()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self._stop.set()
        # stop playback
        try:
            if self._sound:
                self._sound.stop()
        except Exception:
            pass
        # wait a short time for thread to finish
        if self._thread.is_alive():
            self._thread.join(timeout=1)

    def _run(self):
        while not self._stop.is_set():
            if self._sound:
                try:
                    self._sound.play(loops=-1)  # loop during burst
                except Exception:
                    LOG.exception("sound play failed")
            # burst duration
            for _ in range(self.burst_seconds):
                if self._stop.is_set():
                    break
                time.sleep(1)
            # stop burst
            try:
                if self._sound:
                    self._sound.stop()
            except Exception:
                pass
            # wait until next repeat or exit
            for _ in range(self.repeat_interval_seconds):
                if self._stop.is_set():
                    break
                time.sleep(1)
