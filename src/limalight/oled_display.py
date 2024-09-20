import os
import threading
import time
import logging
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
        self.animations_path = "animations/"
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
            frames = []
            animation_dir = os.path.join(self.animations_path, animation_name)
            frame_files = sorted(os.listdir(animation_dir))
            for file in frame_files:
                if file.endswith(".bmp"):
                    frame_path = os.path.join(animation_dir, file)
                    frame_image = Image.open(frame_path).convert("1")
                    # Center the frame on the display
                    centered_frame = self._center_image(frame_image)
                    frames.append(centered_frame)

            delay = 1.0 / fps

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
            self.is_animating = False

    def _center_image(self, img):
        # Create a blank image with the display size
        centered_image = Image.new("1", (self.width, self.height))
        # Calculate the position to center the image
        img_width, img_height = img.size
        x = (self.width - img_width) // 2
        y = (self.height - img_height) // 2
        # Paste the image onto the blank image
        centered_image.paste(img, (x, y))
        return centered_image

    def stop_animation(self):
        self.is_animating = False
        if self.current_thread:
            self.current_thread.join()
            self.current_thread = None

    def display_static_image(self, image_name):
        self.stop_animation()
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        try:
            with self.lock:
                image_path = os.path.join("icons", f"{image_name}.bmp")
                img = Image.open(image_path).convert("L")
                # Invert the image
                img = ImageOps.invert(img)
                # Convert back to '1' mode
                img = img.convert("1")
                centered_image = self._center_image(img)
                self.display.image(centered_image)
                self.display.show()
        except Exception as e:
            logging.error(f"Error displaying image '{image_name}': {e}")

    def display_message(self, message, duration=0, return_to_idle=True):
        self.stop_animation()
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        with self.lock:
            self.draw.rectangle((0, 0, self.width, self.height), outline=0, fill=0)
            # Calculate text position to center it
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

    def display_idle(self):
        self.play_animation("idle", loop=True, fps=2)

    def clear(self):
        self.stop_animation()
        if self.timer and self.timer.is_alive():
            self.timer.cancel()
        with self.lock:
            self.display.fill(0)
            self.display.show()
