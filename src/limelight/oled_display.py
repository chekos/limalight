import threading
import time
import logging
import importlib.resources
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
from .base_display import BaseDisplay

# Attempt to import hardware-specific libraries
try:
    from board import SCL, SDA
    import busio
    import adafruit_ssd1306

    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False


class OLEDDisplay(BaseDisplay):
    def __init__(self):
        if not HARDWARE_AVAILABLE:
            raise RuntimeError("OLED hardware not available.")

        # Initialize the display hardware
        self.i2c = busio.I2C(SCL, SDA)
        self.display = adafruit_ssd1306.SSD1306_I2C(128, 32, self.i2c)
        self.display.fill(0)
        self.display.show()
        self.width = self.display.width
        self.height = self.display.height
        self.image = Image.new("1", (self.width, self.height))
        self.draw = ImageDraw.Draw(self.image)
        self.font = ImageFont.load_default()
        self.lock = threading.Lock()
        self.current_thread = None
        self.timer = None
        self.is_animating = False

        # User asset directories
        self.user_asset_dir = Path.home() / ".limelight"
        self.user_animations_path = self.user_asset_dir / "animations"
        self.user_icons_path = self.user_asset_dir / "icons"

        # Package asset directories
        self.package = "limelight"
        self.package_animations_path = "animations"
        self.package_icons_path = "icons"

    def play_animation(self, animation_name, loop=False, fps=10):
        self.stop_animation()
        self.is_animating = True
        self.current_thread = threading.Thread(
            target=self._animate, args=(animation_name, loop, fps)
        )
        self.current_thread.start()

    def _animate(self, animation_name, loop, fps):
        try:
            frames = []
            delay = 1.0 / fps

            # Attempt to load from user directory
            user_animation_dir = self.user_animations_path / animation_name
            if user_animation_dir.exists():
                frame_files = sorted(user_animation_dir.glob("*.bmp"))
                for frame_file in frame_files:
                    frame_image = Image.open(frame_file).convert("1")
                    centered_frame = self._center_image(frame_image)
                    frames.append(centered_frame)
            else:
                # Load from package resources
                with importlib.resources.path(
                    self.package, f"{self.package_animations_path}/{animation_name}"
                ) as anim_dir:
                    if not anim_dir.exists():
                        logging.error(f"Animation '{animation_name}' not found.")
                        return
                    frame_files = sorted(Path(anim_dir).glob("*.bmp"))
                    for frame_file in frame_files:
                        frame_image = Image.open(frame_file).convert("1")
                        centered_frame = self._center_image(frame_image)
                        frames.append(centered_frame)

            if not frames:
                logging.error(f"No frames found for animation '{animation_name}'.")
                return

            while self.is_animating:
                for frame in frames:
                    with self.lock:
                        self.display.image(frame)
                        self.display.show()
                    time.sleep(delay)
                if not loop:
                    break
        except Exception as e:
            logging.error(f"Error in animation '{animation_name}': {e}")
        finally:
            self.is_animinating = False

    def display_message(self, message, duration=0, return_to_idle=True):
        self.stop_animation()
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        with self.lock:
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
            bbox = self.draw.textbbox((0, 0), message, font=self.font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self.width - text_width) // 2
            y = (self.height - text_height) // 2
            self.draw.text((x, y), message, font=self.font, fill=255)
            self.display.image(self.image)
            self.display.show()
        if duration > 0:
            if return_to_idle:
                self.timer = threading.Timer(duration, self.display_idle)
            else:
                self.timer = threading.Timer(duration, self.clear)
            self.timer.start()

    def display_static_image(self, image_name):
        self.stop_animation()
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        try:
            with self.lock:
                # Attempt to load from user directory
                user_image_path = self.user_icons_path / f"{image_name}.bmp"
                if user_image_path.exists():
                    img = Image.open(user_image_path).convert("1")
                else:
                    # Load from package resources
                    with importlib.resources.path(
                        self.package, f"{self.package_icons_path}/{image_name}.bmp"
                    ) as img_path:
                        if not img_path.exists():
                            logging.error(f"Image '{image_name}' not found.")
                            return
                        img = Image.open(img_path).convert("1")

                img = ImageOps.invert(img.convert("L")).convert("1")
                centered_image = self._center_image(img)
                self.display.image(centered_image)
                self.display.show()
        except Exception as e:
            logging.error(f"Error displaying image '{image_name}': {e}")

    def display_idle(self):
        self.play_animation("idle", loop=True, fps=2)

    def clear(self):
        self.stop_animation()
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        with self.lock:
            self.display.fill(0)
            self.display.show()

    def stop_animation(self):
        self.is_animating = False
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join()
            self.current_thread = None

    def _center_image(self, img):
        centered_image = Image.new("1", (self.width, self.height))
        img_width, img_height = img.size
        x = (self.width - img_width) // 2
        y = (self.height - img_height) // 2
        centered_image.paste(img, (x, y))
        return centered_image
