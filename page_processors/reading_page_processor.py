import sys
import os
import pickle
import time
import random
import requests
import threading
import json
import argparse
import warnings
import colorama
import traceback
import base64
import enum 
import shutil 
    
from coursera_parser_legacy import CourseraParser
from pathlib import Path
from defines import ROOT_DIR
from defines import DOWNLOAD_PATH
from defines import WEBDRIVER_PATH
from defines import COOKIES_PATH
from defines import DEFAULT_SESSION_FNAME
from defines import TIMEOUT
from defines import DEBUG
from defines import ALLOW_LESSON_MISSING
from utils import prepare_file_name
from utils import prepare_dir_name
from utils import get_inner_text
from utils import make_dirs_if_not_exists
from utils import repeater
from utils import fullpage_screenshot
from utils import close_all_windows_except_main
from utils import get_downloaded_file_name
from driver_builder import build_chrome_driver
from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import (
    TimeoutException, 
    WebDriverException, 
    NoSuchElementException, 
    StaleElementReferenceException
)
from page_processors.video_page_processor import VideoPageActions
from page_processors.week_page_processor import WeekPageActions, week_page_items_paths
from selenium.common.exceptions import NoSuchElementException
from colorama import Fore
from datetime import datetime
from page_processors.quiz_page_processor import QuizPageActions
from .utils import resolve_honor_code


from typing import Union
from typing import List
from typing import Dict


colorama.init(autoreset=True)

reading_page_items_paths = {
    "scrolling_element": "#main-container",
    # "left_side_bar": "div:has(> #main-container) > div:nth-child(1)",
    "coursera_bot_chat_button": "#chat-button-container",
    "header_container": "#header-container",
    "close_menu": "div:has(> #main-container) > div:nth-child(1) button[data-track-component='focused_lex_nav_close_button']",
    "open_menu": "button.cds-iconButton-small"
}


def _wait_reading_page(driver:BaseWebDriver):
    print("Loading reading page items")
    wait = WebDriverWait(driver, TIMEOUT)
    
    resolve_honor_code(driver=driver)

    print("Loading scrolling element")
    scrolling_element = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            reading_page_items_paths["scrolling_element"]
        ) 
    )

    print("Loading header container")
    header_container = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            reading_page_items_paths["header_container"]
        )
    )

    print("Loading button to close menu")
    try:
        close_menu_btn = driver.find_element(
            By.CSS_SELECTOR,
            reading_page_items_paths["close_menu"]
        )
    except NoSuchElementException:
        close_menu_btn = None
    
    try:
        open_menu_btn = driver.find_element(By.CSS_SELECTOR, reading_page_items_paths["open_menu"])
    except NoSuchElementException:
        open_menu_btn = None

    print("Loading coursera bot chat button")
    try:
        wait_short = WebDriverWait(driver, 4)
        coursera_bot_chat_button = wait_short.until(
            lambda driver: driver.find_element(
                By.CSS_SELECTOR,
                reading_page_items_paths["coursera_bot_chat_button"]
            ) 
        )
    except TimeoutException:
        coursera_bot_chat_button = None

    print("Reading page loaded")
    return scrolling_element, header_container, close_menu_btn, open_menu_btn, coursera_bot_chat_button


@repeater(TIMEOUT)
def download_from_reading_page(driver: BaseWebDriver, url:str = None, download_path:Path = None):
    # if url is not specified then processcurrent page
    
    assert download_path, "Download path is not specified"

    if url:
        driver.get(url)
    
    time.sleep(5)
    scrolling_element, header_container, close_menu_btn, open_menu_btn, coursera_bot_chat_button = _wait_reading_page(driver)
    
    if not open_menu_btn:
        close_menu_btn.click()

    pdf_name = f"reading_page.pdf"
    image_name = f"reading_screenshot.png"

    base64code = driver.print_page()
    with open(download_path / pdf_name, "wb") as file:
        file.write(base64.b64decode(base64code))

    fullpage_screenshot(
        driver, 
        scrolling_element=scrolling_element,
        removing_elements=filter(lambda x: x is not None, [header_container, coursera_bot_chat_button]),
        file=download_path / image_name)


class ReadingPageActions(enum.Enum):
    @staticmethod
    def download(driver: BaseWebDriver, url:str, download_path:Path):
        download_from_reading_page(driver, url, download_path)
        
        

def demo():
    from defines import DEFAULT_SESSION_FNAME
    from defines import COOKIES_PATH
    
    url = "https://www.coursera.org/learn/robotics-flight/supplement/zGKah/matlab-tutorials-advanced-tools"
    str_datetime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    storage_folder_path = ROOT_DIR / "downloads" / f"test_{str_datetime}"
    
    if storage_folder_path.exists():
        shutil.rmtree(storage_folder_path)

    os.makedirs(storage_folder_path)

    driver = build_chrome_driver(webdriver_path=WEBDRIVER_PATH, headless=False, detach=True)
    coursera_parser = CourseraParser(driver)
    coursera_parser.login_by_cookies(COOKIES_PATH / DEFAULT_SESSION_FNAME)

    
    ReadingPageActions.download(driver, url=url, download_path=storage_folder_path)
    ReadingPageActions.download(driver, url=url, download_path=storage_folder_path)
    
    print("Downloaded files:")
    files = os.listdir(storage_folder_path)
    print("\n".join(files))



def get_args():
    import shutil 
    
    from coursera_parser_legacy import CourseraParser
    curr_date_str = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    
    parser = argparse.ArgumentParser(description="Coursera parser")
    parser.add_argument("-u", "--url", type=str, help="URL of the page to parse")
    parser.add_argument("-p", "--path", default=DOWNLOAD_PATH / curr_date_str, type=str, help="Path to download files")
    parser.add_argument("-c", "--cookies", default=COOKIES_PATH / DEFAULT_SESSION_FNAME, type=str, help="Path to cookies file")
    return parser.parse_args()


def main():
    args = get_args()
    url = args.url
    path = Path(args.path)
    cookies = Path(args.cookies)

    driver = build_chrome_driver(webdriver_path=WEBDRIVER_PATH, headless=False, detach=True)
    coursera_parser = CourseraParser(driver)
    coursera_parser.login_by_cookies(cookies)
    
    os.makedirs(path, exist_ok=True)
    ReadingPageActions.download(driver, url=url, download_path=path)
 

if __name__ == "__main__":
    main()