import pytesseract
import skimage
from skimage.filters import threshold_otsu
import numpy as np
import re

from tkinter import messagebox
import pyautogui
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
        if regex is None:
            regex = r"[\{\[\(]?\d+:?\s*\d+\s*[AP]M\s*[I\]\)\}]?\s*"

        return re.sub(regex, "", self.raw_text)

    def define_frame(self):
        # https://www.reddit.com/r/learnpython/comments/9f4lls/how_to_take_a_screenshot_of_a_specific_window/
        # https://pyautogui.readthedocs.io/en/latest/screenshot.html

        # Prompt user to click top left then top right of area
        print('Please first click on the top left corner of the chat box, the bottom right.')
        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

        with mouse.Listener(on_click=self.on_click) as listener:
            listener.join()

        print('Coordinates grabbed, thank you')

    def take_screenshot(self):
        # the left, top, width, and height of the region to capture:
        im = pyautogui.screenshot(region=(self.x1, self.y1,
                                          self.x2 - self.x1,
                                          self.y2 - self.y1))
        return im

    def on_click(self, x, y, button, pressed):
        if self.x1 != 0 and self.x2 == 0 and pressed:
            self.x2 = x
            self.y2 = y
    
        if self.x1 == 0 and pressed:
            self.x1 = x
            self.y1 = y
        if pressed:
            return False

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

    def validate_frame(self):
        if self.image:
            while True:
                try:
                    self.image.show()
                except SystemError as e:
                    print('Improper frame format.')
                    self.define_frame()
                    self.image = myFrame.take_screenshot()

                if messagebox.askyesno('Please Confirm', 'Is this valid?'):
                    return True
                else:
                    self.define_frame()
                    self.image = myFrame.take_screenshot()
        else:
            return False


myFrame = ChatFrame()

# Explore idea of auto finding chat box with pyautogui image find

myFrame.define_frame()

myFrame.image = myFrame.take_screenshot()

if myFrame.validate_frame():
    myFrame.extract_text()
    myFrame.cycle_shots()
else:
    print('There was an issue determining the frame or image.')
    quit()
