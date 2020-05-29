GW2 Transcriber
==========

Acts as a live writting tool to bring the text inside the chatbox (or the designated area) into a txt file along with screenshots of the dialogue.

The process is performed through [Tesseract OCR](https://github.com/tesseract-ocr/). As such the text will not be 100% correct, but for the most part a quick spellchecker would resolve most issues.

Usage
-----
* First, ensure you have followed all the install instructions in the below section
* Log into a GW2 character and set the chatbox to opaque
* Open a command prompt
    * windows button -> type 'cmd' -> click on `open` or `run as administrator` (see comment below)
* Navigate to the folder for this program
    * type `cd \path\to\this\folder` in the command prompt
* Start this program in a console\cmd with `python gw2Read.py`, follow the prompts.
    * Depending on your install it may be `py gw2Read.py` or whatever other python keyword you have set

It is *Critical* that you run this program at the same level (or above) as GW2. If GW2 is running in administrator mode, then so should this program. A program running in non-admin mode will not be able to grab input given in one in administrator mode.

The obtained dialogue will be placed in the same folder as this program, under `dialogue.txt` and the accompanying screenshots in the subfolder `screenshots\`. At the moment these images serve only as a reference for the user, and have zero impact on the running program; they can thus be deleted at will.

Idealy this program should be run with the text font set to the biggest size, and the chatbox background set to opaque. You will get somewhat useable text without these, however optimal results will come from anything making the text clearer to read.

Initial Install
------
If you do not already have it, you will need to [download and install python](https://www.python.org/downloads/). To be certain it is installed properly (a computer restart may be necessary) open a command prompt and type `python --version`, this should return `Python 3.X.Y`.

With python installed, you will need to make a local copy of this code, you can either download it directly from the download link on the top right of this repository; or make a local clone through git.

This program requires a few 3rd party python libraries, and as such need to be installed prior to running. In your command prompt (ideally having navigated to the folder where this project is located) type and use the following command (which may take a bit to complete).

```
pip install pytesseract scikit-image numpy pyautogui pynput opencv-python pygetwindow
```
Note that it's possible you get warnings along the lines of "requirement already satisfied [...]", that's in no way a problem just means that library is already installed.

Additionally you will need to install [tesseract](https://github.com/UB-Mannheim/tesseract/wiki) (5.0.0 alpha is recomended but 4.X should also work). Do keep in mind the path/folder where tesseract is installed on your computer. If it does *not* match `C:\Program Files\Tesseract-OCR\tesseract.exe`, you will need to put the proper path in gw2Read.py (with any text editor) right below the imports.

Todo
-----
* Make a nice way to pause and stop the program through keyboard shortcuts (user customizable)
* Do some more text parsing
    * Probably move it into another module and allow for user regex additions
