import abc


class BaseDisplay(abc.ABC):
    @abc.abstractmethod
    def play_animation(self, animation_name, loop=False, fps=10):
        pass

    @abc.abstractmethod
    def display_message(self, message, duration=0, return_to_idle=True):
        pass

    @abc.abstractmethod
    def display_static_image(self, image_name):
        pass

    @abc.abstractmethod
    def clear(self):
        pass

    @abc.abstractmethod
    def stop_animation(self):
        pass
