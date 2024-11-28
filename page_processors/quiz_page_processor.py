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

from pathlib import Path
from defines import ROOT_DIR
from defines import DOWNLOAD_PATH
from defines import WEBDRIVER_PATH
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
from .utils import resolve_honor_code

from typing import Union
from typing import List
from typing import Dict


colorama.init(autoreset=True)


quiz_page_items_paths = {
    "open_quiz_button": "button[data-testid='CoverPageActionButton'][type='button']",
    "exit_quiz_button": "div[data-classname='tunnelvision-window-0'] .rc-TunnelVisionClose",
    "scrolling_element": "#TUNNELVISIONWRAPPER_CONTENT_ID",
    "honor_code_accept_btn": ".cds-Dialog-dialog .align-right .cds-button-disableElevation",
    "start_retry_attempt_confirm_btn": ".cds-Modal-container button[data-testid='StartAttemptModal__primary-button']"
}


def _wait_quiz_page_before_quiz_starting(driver:BaseWebDriver):
    print("Loading quiz page items")
    wait = WebDriverWait(driver, TIMEOUT)
    
    resolve_honor_code(driver)

    print("Loading open quiz button")
    open_quiz_btn = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            quiz_page_items_paths["open_quiz_button"]
        ) 
    )


    print("Quiz page loaded")
    return open_quiz_btn


def _wait_quiz_page_after_quiz_starting(driver:BaseWebDriver):
    print("Loading qiuiz tasks page items")
    wait = WebDriverWait(driver, TIMEOUT)

    
    print("Loading exit quiz button")
    exit_quiz_btn = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            quiz_page_items_paths["exit_quiz_button"]
        ) 
    )

    print("Loading quiz tasks scrolling element")
    quiz_scrolling_element = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            quiz_page_items_paths["scrolling_element"]
        ) 
    )

    print("Quiz tasks page loaded")
    return exit_quiz_btn, quiz_scrolling_element



@repeater(TIMEOUT)
def download_from_quiz_page(driver: BaseWebDriver, url:str, download_path:Path):
    driver.get(url)
    start_quiz_btn = _wait_quiz_page_before_quiz_starting(driver)

    try:
        honor_code_btn = driver.find_element(By.CSS_SELECTOR, quiz_page_items_paths["honor_code_accept_btn"])
        honor_code_btn.click()
    except NoSuchElementException:
        pass

    start_quiz_btn.click()
    time.sleep(1)
    
    button_text = start_quiz_btn.text
    if "retry" in button_text.lower():
        confirm_btn = driver.find_element(
            By.CSS_SELECTOR, 
            quiz_page_items_paths["start_retry_attempt_confirm_btn"]
        )
        confirm_btn.click()
        time.sleep(1)
    
    elif "resume" in button_text.lower():
        pass

    exit_quiz_btn, scrolling_element = _wait_quiz_page_after_quiz_starting(driver)
    time.sleep(5)

    image_name = f"quiz_screenshot.png"

    fullpage_screenshot(
        driver, 
        scrolling_element=scrolling_element,
        file=download_path / image_name,
        time_delay=2)
    
    exit_quiz_btn.click()
    
    
class QuizPageActions:
    @staticmethod
    def download(driver: BaseWebDriver, url:str, download_path:Path):
        return download_from_quiz_page(driver, url, download_path)