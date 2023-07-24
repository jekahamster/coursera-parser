import os
import pathlib

ROOT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True
ALLOW_LESSON_MISSING = False

DOWNLOAD_PATH = ROOT_DIR / "downloads"
COOKIES_PATH = ROOT_DIR / "cookies"
WEBDRIVER_PATH = ROOT_DIR / "webdrivers" / "chromedriver_106.exe"
EXTENSIONS_PATH = ROOT_DIR / "extensions"
DEFAULT_SESSION_FNAME = "last-saved.pkl"
TIMEOUT = 120
