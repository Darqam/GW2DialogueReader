import pytesseract
import skimage
from skimage.filters import threshold_otsu
import numpy as np

# These imports are explicit purely for exe purposes
import numpy.random.common
import numpy.random.bounded_integers

import pyautogui
import pygetwindow as gw
import cv2
from pynput import mouse, keyboard

import yaml
from pathlib import Path

import time
import datetime
from os import path, mkdir, sep
import sys

# Custom module
from clean_output import clean


# Tiny bit of work to allow loading tupples from yaml
class PrettySafeLoader(yaml.SafeLoader):
    def construct_python_tuple(self, node):
        return tuple(self.construct_sequence(node))


PrettySafeLoader.add_constructor(
    u'tag:yaml.org,2002:python/tuple',
    PrettySafeLoader.construct_python_tuple)


# Now to the core of it all
class ChatFrame:
    """
    Class describing the virtual GW2 chatbox position, image, and content
    """
    def __init__(self):
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0
        self.width = 0
        self.height = 0

        self.valid_frame = False
        self.confidence_level = 0.8

        self.image = None
        self.raw_text = None
        self.parsed_text = None

        self.last_content = None
        self.last_line = None
        self.last_entry_time = None

        # If the user wants to make use of custom regex, make custom_regexs a list of tuples
        # The first entry in the tuple being the `find` and the 2nd the `replace` strings
        self.custom_regexs = None
        self.use_default_regex = True

        self.d_filepath = f"{Path('./dialogue.txt')}"
        self.ss_folderpath = f"{Path('./screenshots/')}{sep}"
        self.header_interval_time = 300  # in seconds
        self.read_interval = 10
        self.tesseract_filepath = f"{Path('C:/Program Files/Tesseract-OCR/tesseract.exe')}"

        # Load user configs
        self.load_configs()
        # Make sure we have a valid screenshots folder
        self.verify_folder()
        # Make a new entry in the dialogue txt file
        self.new_file_entry()

    def load_configs(self):
        with open(Path("./config.yaml"), 'r') as stream:
            try:
                config = yaml.load(stream, Loader=PrettySafeLoader)
                self.d_filepath = Path(config['dialogue_filepath'])
                self.ss_folderpath = f"{Path(config['screenshot_folderpath'])}{sep}"
                self.header_interval_time = config['time_header_interval']
                self.read_interval = config['read_interval']
                self.tesseract_filepath = f"{Path(config['tesseract_filepath'])}"
                self.confidence_level = config['confidence_level']
                self.custom_regexs = config['user_regex']
                self.use_default_regex = config['use_default_regex']

                # Give explicit path to tesseract exe
                pytesseract.pytesseract.tesseract_cmd = self.tesseract_filepath
            except yaml.YAMLError as exc:
                print(exc)
                pyautogui.alert(text='There was an error loading config.yaml, please ensure it is filled out '
                                     'properly, aborting.',
                                title='Error',
                                button='OK')
                sys.exit(1)

    def new_file_entry(self):
        """Adds a datetime header to the dialogue file."""
        with open(self.d_filepath, 'a') as file:
            cur_date = datetime.datetime.fromtimestamp(time.time())
            file.write('\n\n---{0}---\n'.format(cur_date.strftime('%Y-%m-%d %H:%M:%S')))
            self.last_entry_time = time.time()

    def verify_folder(self):
        """Verifies that screenshot folder exists, if not attempts to create it."""
        if not path.isdir(self.ss_folderpath):
            try:
                mkdir(self.ss_folderpath)
            except Exception as err:
                print(err)
                pyautogui.alert(text='Could not create or find the folder {0}, aborting.'.format(self.ss_folderpath),
                                title='Error',
                                button='OK')
                sys.exit(1)

    def reset_frame(self):
        """Resets all frame related coordinates to 0."""
        self.x1 = 0
        self.x2 = 0
        self.y1 = 0
        self.y2 = 0
        self.width = 0
        self.height = 0

    def get_frame(self):
        """Will attempt to grab the frame automatically, if fails prompts user for further instructions."""
        # Try to auto find the frame first
        self.auto_frame()

        # If auto finding chat fails, prompt user to show it
        while not self.valid_frame:
            # create a black image, needed to pull focus of GW2 window
            open_cv_image = np.zeros(shape=[512, 512, 3], dtype=np.uint8)
            cv2.imshow('image', open_cv_image)

            # Do some funky stuff to make the image popup above GW2 window
            try:
                window = gw.getWindowsWithTitle("image")[0]
                if window:
                    w_width = window.width
                    w_height = window.height
                    window.minimize()
                    window.maximize()
                    window.resizeTo(w_width, w_height)
            except gw.PyGetWindowException as e:
                print(e)

            response = pyautogui.confirm(text='Could not find the chat box automatically. Do you wish to retry on '
                                              'automatic mode or manual?',
                                         title='GW2 Read Error',
                                         buttons=['Automatic', 'Manual', 'Abort'])
            cv2.destroyAllWindows()
            if response == 'Abort':
                sys.exit(0)
            elif response == 'Manual':
                self.manual_frame()
            elif response == 'Automatic':
                pyautogui.confirm(text='Please ensure that the chat box is up and in opaque mode before dismissing '
                                       'this window',
                                  title='GW2 Read Error',
                                  buttons=['Ok'])
                self.auto_frame()

            if self.width >= 10 and self.height >= 10:
                self.valid_frame = True

    def auto_frame(self):
        """Will attempt to automatically find the GW2 chatbox based on two reference images.
        If found, will set appropriate frame information."""

        try:
            window = gw.getWindowsWithTitle("Guild Wars 2")[0]
            if window:
                window.maximize()
                window.activate()
        except IndexError as e:
            pyautogui.alert(text='Could not find a window titled "Guild Wars 2", aborting.', title='Error',
                            button='OK')
            sys.exit(1)

        # wait 0.5 seconds for the window to actually be in frame
        # failing to do this can result in just a black box
        time.sleep(0.5)

        bl = pyautogui.locateOnScreen('./reference/bl_corner.png', confidence=self.confidence_level)
        tr = pyautogui.locateOnScreen('./reference/tr_corner.png', confidence=self.confidence_level)
        if bl is not None and tr is not None:
            self.x1 = bl.left + bl.width / 2
            self.y1 = bl.top

            self.x2 = tr.left + tr.width / 2
            self.y2 = tr.top + tr.height

            self.width = self.x2 - bl.left - bl.width/2
            self.height = self.y1 - self.y2

            self.valid_frame = True
        else:
            self.width = 0
            self.height = 0

    def manual_frame(self):
        """Prompts user, then creates 2 subsequent listeners for click events (see on_click())."""
        # https://www.reddit.com/r/learnpython/comments/9f4lls/how_to_take_a_screenshot_of_a_specific_window/
        # https://pyautogui.readthedocs.io/en/latest/screenshot.html

        # Prompt user to click top left then top right of area
        pyautogui.confirm(text='Please click on the bottom left corner of the chat box, then the top right corner '
                               'after dismissing this window.',
                          title='GW2Transcriber info',
                          buttons=['Ok'])
        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

    def on_click(self, x, y, button, pressed):
        """Will trigger from click events in manual_frame(). It will set frame coordinates assuming
        the first click is the bottom left of the chat box, and 2nd top right."""
        if self.x1 != 0 and self.x2 == 0 and pressed:
            self.x2 = x
            self.y2 = y

            self.width = self.x2 - self.x1
            self.height = self.y1 - self.y2

        if self.x1 == 0 and pressed:
            self.x1 = x
            self.y1 = y
        if pressed:
            return False

    def validate_frame(self):
        """Presents the grabbed frame as an image to the user and prompts for confirmation if
        the image shows the proper chat box. If this is not satisfied, prompts for further action."""
        if self.image:
            while True:
                try:
                    open_cv_image = np.array(self.image)
                    # Convert RGB to BGR
                    open_cv_image = open_cv_image[:, :, ::-1].copy()
                    cv2.imshow('image', open_cv_image)

                    # Do some funky stuff to make the image popup above GW2 window
                    try:
                        window = gw.getWindowsWithTitle("image")[0]
                        if window:
                            w_width = window.width
                            w_height = window.height
                            window.minimize()
                            window.maximize()
                            window.resizeTo(w_width, w_height)
                    except gw.PyGetWindowException as e:
                        print(e)
                except SystemError as e:
                    print('Improper frame format.', e)
                    if not self.auto_frame():
                        self.get_frame()
                    self.image = self.take_screenshot()

                response = pyautogui.confirm(text='Does this image show the full text area of the chat box',
                                             title='Please confirm',
                                             buttons=['Yes', 'Retry auto', 'Try Manual', 'Quit'])
                cv2.destroyAllWindows()
                if response == 'Yes':
                    return True
                elif response == 'Retry auto':
                    # Reduce required confidence level on each retry
                    self.confidence_level -= 0.05

                    pyautogui.confirm(text='Please ensure that the chat box is up and in opaque mode before dismissing'
                                           'this window',
                                      title='GW2 Read Error',
                                      buttons=['Ok'])
                    self.reset_frame()
                    self.get_frame()
                    self.image = self.take_screenshot()
                elif response == 'Try Manual':
                    self.reset_frame()
                    self.manual_frame()
                    self.image = self.take_screenshot()
                elif response == 'Quit':
                    sys.exit(0)
        else:
            return False

    def take_screenshot(self):
        """Will take a screenshot based on saved frame coordinates"""
        # the left, top, width, and height of the region to capture:
        im = pyautogui.screenshot(region=(self.x1, self.y2,
                                          self.width,
                                          self.height))
        return im

    def extract_text(self):
        """
        Grabs the stored image, optimizes image for OCR and runs it through tesseract.
        :return: [string] The raw text string outputed by Tesseract
        """
        # https://tesseract-ocr.github.io/tessdoc/ImproveQuality

        # First convert image to numpy array
        img = np.array(self.image)

        # Convert to grayscale and invert (to get black text on white bckg)
        gray = skimage.util.invert(skimage.color.rgb2gray(img))

        # Use Otsu thresholding and convert to binary
        thresh_otsu = gray > threshold_otsu(gray)

        self.raw_text = pytesseract.image_to_string(thresh_otsu).replace('\n\n', '\n')
        return self.raw_text

    def cycle_shots(self, timer=10):
        """
        Endless loop which calls for screenshot and text extraction+cleanup
        Will verify there is new text grabbed in the latest image
        If not, continue on, if yes then print to file and save screenshot
        :param timer: The delay between read intervals (in seconds)
        """
        while True:
            self.image = self.take_screenshot()

            self.extract_text()
            out = clean(self.raw_text, use_defaults=self.use_default_regex, custom=self.custom_regexs)

            if out is False:
                out = self.raw_text

            lines = out.split('\n')
            last_line = lines[-1]
            new_lines = []

            if self.last_content is None:
                # Write text to file
                # save screenshot
                self.print_to_file(lines)
                self.save_screenshot()

                self.last_line = last_line
                self.last_content = '\n'.join(lines)
            elif last_line != self.last_line:
                # Loop over new lines from the end until something matches
                # Remove everything from new lines from where the first match occurs
                # (i.e this ignores already parsed text from previous screenshots)
                for idx, line in enumerate(reversed(lines)):
                    if line not in self.last_content:
                        continue
                    else:
                        new_lines = lines[len(lines) - idx:len(lines)]
                        break

                if len(new_lines) > 0:
                    # First check if it's been more than the requested header delay
                    if time.time() - self.last_entry_time > self.header_interval_time:
                        # Add a new time header
                        self.new_file_entry()

                    self.print_to_file(new_lines)
                    self.save_screenshot()

                    self.last_line = last_line
                    self.last_content = '\n'.join(new_lines)

            # Sleep for 'timer' seconds since the last loop iteration
            # Note that this isn't a true "consistent" delay since it depends on processing time
            # I, however, rather keep it as such since a) meh, and b) prevents possible double up
            time.sleep(timer)

    def print_to_file(self, lines=None):
        """
        Will print the provided lines to the appropriate dialogue text file
        :param lines: a list of strings, text to be written to the file
        """
        if lines is None:
            return

        with open(self.d_filepath, 'a') as file:
            print('Adding new text to file.')
            file.write('\n'.join(lines))

    def save_screenshot(self):
        """Saves the screenshot of the chat frame with a datetime filename."""
        cur_date = datetime.datetime.fromtimestamp(time.time())
        filename = '{0}{1}.jpg'.format(self.ss_folderpath, cur_date.strftime('%Y-%m-%d_%H-%M-%S'))
        self.image.save(filename)


myFrame = ChatFrame()
try:
    myFrame.get_frame()
    myFrame.image = myFrame.take_screenshot()
except Exception as e:
    print(e)

if myFrame.image:
    myFrame.validate_frame()
    pyautogui.confirm(text='Ok, let\'s go.', title='Eyy',
                      buttons=['*push the button*'])
    myFrame.extract_text()

    #stop_listener = keyboard.Listener()

    myFrame.cycle_shots()
else:
    pyautogui.alert(text='There was an issue determining the frame or image, aborting.', title='Error',
                    button='OK')
    sys.exit(1)
