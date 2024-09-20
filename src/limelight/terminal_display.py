import threading
import time
from .base_display import BaseDisplay


class TerminalDisplay(BaseDisplay):
    def __init__(self):
        self.lock = threading.Lock()
        self.current_thread = None
        self.timer = None
        self.is_animating = False

    def play_animation(self, animation_name, loop=False, fps=10):
        self.stop_animation()
        self.is_animating = True
        self.current_thread = threading.Thread(
            target=self._animate, args=(animation_name, loop, fps)
        )
        self.current_thread.start()

    def _animate(self, animation_name, loop, fps):
        try:
            delay = 1.0 / fps
            frames = [f"Frame {i}" for i in range(1, 5)]  # Simulated frames
            while self.is_animating:
                for frame in frames:
                    with self.lock:
                        print(f"[Animation: {animation_name}] {frame}")
                    time.sleep(delay)
                if not loop:
                    break
        finally:
            self.is_animating = False

    def display_message(self, message, duration=0, return_to_idle=True):
        self.stop_animation()
        with self.lock:
            print(f"[Message] {message}")
        if duration > 0:
            time.sleep(duration)
            if return_to_idle:
                self.play_animation("idle", loop=True, fps=2)
            else:
                self.clear()

    def display_static_image(self, image_name):
        self.stop_animation()
        with self.lock:
            print(f"[Static Image] Displaying image '{image_name}'")

    def clear(self):
        with self.lock:
            print("[Display Cleared]")

    def stop_animation(self):
        self.is_animating = False
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join()
            self.current_thread = None
