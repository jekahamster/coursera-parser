import os
import pathlib
import sys

ROOT_DIR = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True
ALLOW_LESSON_MISSING = False

DOWNLOAD_PATH = ROOT_DIR / "downloads"
COOKIES_PATH = ROOT_DIR / "cookies"
if sys.platform == "darwin":  # macOS
    WEBDRIVER_PATH = ROOT_DIR / "webdrivers" / "chromedriver"
else:
    WEBDRIVER_PATH = ROOT_DIR / "webdrivers" / "chromedriver.exe"
EXTENSIONS_PATH = ROOT_DIR / "extensions"
DEFAULT_SESSION_FNAME = "last-saved.pkl"
TIMEOUT = 120
# TIMEOUT = 30
DIRNAME_CHAR_COUNT = 100
