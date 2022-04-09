import keyboard
import queue


class KeyboardEvent(keyboard.KeyboardEvent):
    """
    Extending keyboard.KeyboardEvent to add a .from_json() method
    """
    @classmethod
    def from_json(cls, attrs):
        return KeyboardEvent(attrs['event_type'], attrs['scan_code'], name=attrs['name'],
                             time=attrs['time'], is_keypad=attrs['is_keypad'])

    @classmethod
    def from_keyboard_event(cls, event):
        """
        Takes a regular keyboard.KeyboardEvent and creates a new instance of our
        KeyboardEvent class, with the same data
        """
        return KeyboardEvent(event.event_type, event.scan_code, name=event.name,
                             time=event.time, is_keypad=event.is_keypad)


class KeystrokeRecorder(object):
    """
    Simple wrapper around the 'keyboard' module to start/stop
    recording of keyboard events
    """
    def __init__(self):
        self._queue = queue.Queue()

    def _on_keypress(self, e):
        self._queue.put(KeyboardEvent.from_keyboard_event(e))

    def start(self):
        keyboard.hook(self._on_keypress)

    def stop(self):
        keyboard.unhook(self._on_keypress)

    @property
    def events(self):
        return list(self._queue.queue)

