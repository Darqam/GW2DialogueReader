from pynput import keyboard


class Hotkey:
    """
    Class used to handle the hotkey listening
    """
    def __init__(self, frame):

        # The key combination to check
        self.frame = frame
        self.hotkey = frame.hotkey
        self.COMBINATION = [{keyboard.Key.alt, keyboard.KeyCode(char=self.hotkey)},
                            {keyboard.Key.alt_l, keyboard.KeyCode(char=self.hotkey)},
                            {keyboard.Key.alt_r, keyboard.KeyCode(char=self.hotkey)}]
        # The currently active modifiers
        self.current = set()

    def on_press(self, key):
        # If the key press is part of any in the COMBINATION array
        if any([key in comb for comb in self.COMBINATION]):
            self.current.add(key)
            # If we now have all of the keys in one of the entries of the array
            if any(all(k in self.current for k in comb) for comb in self.COMBINATION):
                self.frame.toggle_pause()
                # remove everything in the 'current' set (i.e reset hotkey)
                self.current.clear()

    def on_release(self, key):
        try:
            self.current.remove(key)
        except KeyError:
            pass
