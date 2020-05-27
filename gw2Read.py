import pytesseract
import skimage
from skimage.filters import threshold_otsu
import numpy as np
import re

import pyautogui
import pygetwindow as gw
import cv2
from pynput import mouse

import time
import datetime
from os import path, mkdir

# Give explicit path to tesseract exe
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class ChatFrame:
    """
    Information pertaining to the chat box frame and examination of
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

        self.d_filepath = './dialogue.txt'
        self.ss_folderpath = './screenshots/'
        self.header_interval_time = 300  # in seconds

        # Make sure we have a valid screenshots folder
        self.verify_folder()
        # Make a new entry in the dialogue txt file
        self.new_file_entry()

    def new_file_entry(self):
        with open(self.d_filepath, 'a') as file:
            cur_date = datetime.datetime.fromtimestamp(time.time())
            file.write('\n\n---{0}---\n'.format(cur_date.strftime('%Y-%m-%d %H:%M:%S')))
            self.last_entry_time = time.time()

    def verify_folder(self):
        if not path.isdir(self.ss_folderpath):
            try:
                mkdir(self.ss_folderpath)
            except:
                print('Could not create or find the folder {0}'.format(self.ss_folderpath))
                quit()

    def get_frame(self):
        # Try to auto find the frame first
        self.auto_frame()

        # If auto finding chat fails, prompt user to show it
        while not self.valid_frame:
            window = gw.getWindowsWithTitle("Guild Wars 2")[0]
            if window:
                window.minimize()
            response = pyautogui.confirm(text='Could not find the chat box automatically. Do you wish to retry on '
                                              'automatic mode or manual?',
                                         title='GW2 Read Error',
                                         buttons=['Automatic', 'Manual', 'Abort'])
            if response == 'Abort':
                quit()
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
        window = gw.getWindowsWithTitle("Guild Wars 2")[0]
        if window:
            window.maximize()
            window.activate()

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
        # https://www.reddit.com/r/learnpython/comments/9f4lls/how_to_take_a_screenshot_of_a_specific_window/
        # https://pyautogui.readthedocs.io/en/latest/screenshot.html

        # Prompt user to click top left then top right of area
        print('Please first click on the bottom left corner of the chat box, then the top right corner.')
        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

        print('Coordinates grabbed, thank you')

    def on_click(self, x, y, button, pressed):
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
                    if not myFrame.auto_frame():
                        myFrame.get_frame()
                    self.image = myFrame.take_screenshot()

                response = pyautogui.confirm(text='Is this valid?', title='Please confirm',
                                             buttons=['OK', 'Retry'])
                cv2.destroyAllWindows()
                if response == 'OK':
                    return True
                else:
                    myFrame.get_frame()
                    self.image = myFrame.take_screenshot()
        else:
            return False

    def take_screenshot(self):
        # the left, top, width, and height of the region to capture:
        im = pyautogui.screenshot(region=(self.x1, self.y2,
                                          self.width,
                                          self.height))
        return im

    def extract_text(self):
        # https://tesseract-ocr.github.io/tessdoc/ImproveQuality

        # First convert image to numpy array
        img = np.array(self.image)

        # Convert to grayscale and invert (to get black text on white bckg)
        gray = skimage.util.invert(skimage.color.rgb2gray(img))

        # Use Otsu thresholding and convert to binary
        thresh_otsu = gray > threshold_otsu(gray)

        self.raw_text = pytesseract.image_to_string(thresh_otsu).replace('\n\n', '\n')
        # print(self.raw_text)
        return self.raw_text

    def sanitize_text(self, regex=None):
        cleaned_string = self.raw_text
        if regex is None:
            # regex for time in 12h or 24h
            # regex for channel tag [m], [s], etc
            # [G], [G1/2/3/4/5], [S], [M], [T]
            regex_tag = r"[\[\(\{]?\s*[GSMWTP][1-5]?\s*[\]\)\]]"
            regex_time = r"[\[\(\{I]?\d+\s*:\s*\d+\s*[AP]?M?[\]\}\)I]?\s*"
            regex_guild = r"[\[\(\{]?\s*[A-Za-z]{1-4}?\s*[\]\)\]]"

            cleaned_string = re.sub(regex_time, "", cleaned_string)
            cleaned_string = re.sub(regex_tag, "", cleaned_string)
            cleaned_string = re.sub(regex_guild, "", cleaned_string)
            return cleaned_string

        return re.sub(regex, "", cleaned_string)

    def cycle_shots(self, timer=10):
        while True:
            self.image = self.take_screenshot()

            self.extract_text()
            out = self.sanitize_text()

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
        if lines is None:
            return

        with open(self.d_filepath, 'a') as file:
            print('Adding new text to file.')
            file.write('\n'.join(lines))

    def save_screenshot(self):
        cur_date = datetime.datetime.fromtimestamp(time.time())
        filename = '{0}{1}.jpg'.format(myFrame.ss_folderpath, cur_date.strftime('%Y-%m-%d_%H-%M-%S'))
        self.image.save(filename)


myFrame = ChatFrame()

myFrame.get_frame()
myFrame.image = myFrame.take_screenshot()

if myFrame.image:
    myFrame.validate_frame()
    myFrame.extract_text()
    myFrame.cycle_shots()
else:
    print('There was an issue determining the frame or image.')
    quit()
