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
from page_processors.reading_page_processor import ReadingPageActions
from page_processors.quiz_page_processor import QuizPageActions
from selenium.common.exceptions import NoSuchElementException
from colorama import Fore
from datetime import datetime

from typing import Union
from typing import List
from typing import Dict


colorama.init(autoreset=True)

reading_page_items_paths = {
    "scrolling_element": "#main-container",
    # "left_side_bar": "div:has(> #main-container) > div:nth-child(1)",
    "coursera_bot_chat_button": "#coursera-coach-widget",
    "header_container": "#header-container",
    "close_menu": "div:has(> #main-container) > div:nth-child(1) button[data-track-component='focused_lex_nav_close_button']",
    "open_menu": "#main-container button[data-track-component='focused_lex_nav_open_button']"
}

login_page_items_paths = {
    "login_email_field": "input[name='email']",
    "login_password_field": "input[name='password']",
    "login_button_send": "button[type='submit']"
}


lab_page_items_paths = {
    "scrolling_element": "#main-container",
    "load_notebook_button": "#main-container button[role='link']",
    "coursera_bot_chat_button": "#coursera-coach-widget",
    "honor_code_accept_btn": "div.cds-Modal-container button[data-test='continue-button']"
}


jupter_notebook_page_items_paths = {
    "scrolling_element": "#notebook",
    "lab_files_button": "button[data-testid='framed-lab-header-download-files-button']",
    "download_all_files_button": "div[data-panel-id='right-panel'] button[data-track-component='lab_files_download']",
    "notebook_iframe": "iframe[title='lab']",
    "close_updates_info_button": ".c-modal-content button"
}


# available_lesson_types = list(map(lambda x: x.lower(), [
#     "",                                 # screenshot
#     "video",                            # video
#     "programming assignment",           # None
#     "practice programming assignment",  # None
#     "quiz",                             # Quiz
#     "ungraded external tool",           # ?
#     "reading",                          # screenshot
#     "peer-graded assignment",           # ?
#     "review your peers",                # ?
#     "Discussion Prompt",                # screenshot
#     "Practice Quiz",                    # Quiz
#     "Graded External Tool",             # ?
#     "Ungraded Plugin",
#     "Ungraded App Item",                    # https://www.coursera.org/learn/machine-learning-probability-and-statistics/home/week/1
#     "Lab",                                  # Upper url. Like programming assignment
#     "Graded App Item",
#     "Guided Project",
#     "Practice Assignment",
#     "Graded Assignment"                 # quiz
# ]))

# available_lesson_type_classes = list(map(lambda x: x.lower(), [
#     "WeekSingleItemDisplay-lecture",
#     "WeekSingleItemDisplay-supplement",
#     "WeekSingleItemDisplay-lecture",
#     "WeekSingleItemDisplay-discussionPrompt",
#     "WeekSingleItemDisplay-exam",
#     "WeekSingleItemDisplay-ungradedWidget",
#     "WeekSingleItemDisplay-ungradedLti",         # Ungraded App Item
#     "WeekSingleItemDisplay-ungradedLab",
#     "WeekSingleItemDisplay-quiz",
#     "WeekSingleItemDisplay-gradedProgramming",
#     "WeekSingleItemDisplay-ungradedProgramming",
#     "WeekSingleItemDisplay-gradedLti",           
#     "WeekSingleItemDisplay-ungradedAssignment",      # Practice Assignment
#     "WeekSingleItemDisplay-staffGraded",             # Quiz
# ]))



# lesson_type2action = {
#     "": "screenshot",
#     "video": "video",
#     # "programming assignment": "code",
#     # "practice programming assignment": "code",
#     "programming assignment": "screenshot",
#     "practice programming assignment": "screenshot",
#     "quiz": "quiz",
#     "ungraded external tool": None, # ?
#     "reading": "screenshot",
#     "peer-graded assignment": None,
#     "review your peers": None,
#     "Discussion Prompt": "screenshot",
#     "Practice Quiz": "quiz",
#     "Graded External Tool": None,
#     "Ungraded Plugin": "screenshot", # (youtube link) https://www.coursera.org/learn/differential-equations-engineers/ungradedWidget/NLLHm/defining-the-exponential-logarithm-sine-and-cosine-functions-using-odes
#     "Ungraded App Item": "screenshot", # https://www.coursera.org/learn/machine-learning-probability-and-statistics/home/week/1
#     "Lab": "code", 
#     "Graded App Item": None,
#     "Guided Project": None,
#     # "Practice Assignment": "code",
#     "Practice Assignment": "screenshot",
#     "Graded Assignment": "quiz"
# }




def _wait_login_page(driver:BaseWebDriver):
    print("Loading login page items")
    wait = WebDriverWait(driver, TIMEOUT)

    print("Loading email field")
    email_field = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            login_page_items_paths["login_email_field"]
        ) 
    )

    print("Loading password field")
    password_field = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            login_page_items_paths["login_password_field"]
        )
    )

    print("Loading send button")
    button_send = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            login_page_items_paths["login_button_send"]
        )
    )

    print("Login page loaded")
    return email_field, password_field, button_send


def _wait_programming_assignment_page(driver:BaseWebDriver):
    print("Loading lab page items")
    wait = WebDriverWait(driver, TIMEOUT)

    print("Loading scrolling element")
    scrolling_element = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            lab_page_items_paths["scrolling_element"]
        ) 
    )

    print("Loading load notebook button")
    load_notebook_btn = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            lab_page_items_paths["load_notebook_button"]
        ) 
    )

    try:
        honor_code_accept_btn = driver.find_element(By.CSS_SELECTOR, lab_page_items_paths["honor_code_accept_btn"])
    except NoSuchElementException:
        honor_code_accept_btn = None

    print("Lab page loaded")
    return scrolling_element, load_notebook_btn, honor_code_accept_btn


def _wait_jupter_notebook_page(driver:BaseWebDriver):
    print("Loading jupyter notebook page items")
    wait = WebDriverWait(driver, TIMEOUT)

    print("Loading notebook iframe")
    notebook_iframe = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            jupter_notebook_page_items_paths["notebook_iframe"]
        ) 
    )

    print("Loading lab files button")
    lab_files_btn = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            jupter_notebook_page_items_paths["lab_files_button"]
        ) 
    )

    print("Jupyter notebook page loaded")
    return notebook_iframe, lab_files_btn


class CourseraParser:
    def __init__(self, webdriver:BaseWebDriver = None):
        self.driver = webdriver or build_chrome_driver(
                                        webdriver_path=WEBDRIVER_PATH, 
                                        headless=True, 
                                        tor=False, 
                                        no_logging=True, 
                                        detach=False, 
                                        download_path=DOWNLOAD_PATH)

    def user_control(self, url:str = None):
        if url:
            self.driver.get(url)
        
        os.system("pause")

    def save_cookies(self, path:Path):
        if type(path) == str:
            path = Path(path)

        with open(path, "wb") as file:
            pickle.dump(self.driver.get_cookies(), file)

    def load_cookies(self, path:Path):
        if type(path) == str:
            path = Path(path)

        with open(path, "rb") as file:
            cookies = pickle.load(file)

        for cookie in cookies:
            self.driver.add_cookie(cookie)

    def login_by_cookies(self, path:Path):
        url = "https://www.coursera.org/"
        self.driver.get(url)
        self.load_cookies(path)

    def login_by_site(self, email:str = None, password:str = None):
        url = "https://www.coursera.org/?authMode=login"
        self.driver.get(url)
        
        if not email:
            email = input("Email: ").strip()

        if not password:
            password = input("Password: ").strip()

        email_field, password_field, button_send = _wait_login_page(self.driver)

        email_field.send_keys(email)
        password_field.send_keys(password)
        button_send.click()
        self.user_control()

    def change_download_path(self, download_path:Path):
        self.driver.command_executor._commands['send_command'] = (
            'POST', '/session/$sessionId/chromium/send_command')

        params = {
            'cmd': 'Page.setDownloadBehavior',
            'params': { 'behavior': 'allow', 'downloadPath': str(download_path) }
        }
        self.driver.execute("send_command", params)

    def _toggle_dropdown_menu(self, css_selector:str):
        dropdown_btn = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        dropdown_btn.click()

    def _select_subtitles_lang(self, lang:str, css_selector:str):
        # #select-language
        select = Select(self.driver.find_element(By.CSS_SELECTOR, css_selector))
        options = select.options
    
        for option in options: 
            option = option.text
            
            if lang.lower() in option.lower():
                select.select_by_visible_text(option)
                return True
                
        return False

   
    @repeater(TIMEOUT)
    def download_from_jupyter_notebook_page(self, url:str = None, download_path:Path = None):
        # if url is not specified then processcurrent page

        assert download_path, "Download path is not specified"
        if url: 
            self.driver.get(url)
        

        notebook_iframe, lab_files_btn = _wait_jupter_notebook_page(self.driver)

        time.sleep(10)

        try:
            close_updates_info_btn = self.driver.find_element(By.CSS_SELECTOR, jupter_notebook_page_items_paths["close_updates_info_button"])
            close_updates_info_btn.click()
        except NoSuchElementException:
            pass

        # TODO: use iframe to get screenshot
        # fullpage_screenshot(
        #     self.driver,
        #     scrolling_element=scrolling_element,
        #     file=download_path / f"jupyetr_file_screenshot.png")

        time.sleep(1)

        lab_files_btn.click()
        time.sleep(2)

        download_all_files_btn = self.driver.find_element(By.CSS_SELECTOR, jupter_notebook_page_items_paths["download_all_files_button"])
        download_all_files_btn.click()

    @repeater(TIMEOUT)
    def download_from_programming_assignment_page(self, url:str, download_path:Path):
        self.driver.get(url)
        self.change_download_path(download_path)
        scrolling_element, load_notebook_btn, honor_code_accept_btn = _wait_programming_assignment_page(self.driver)

        if honor_code_accept_btn:
            honor_code_accept_btn.click()

        self.download_from_reading_page(download_path=download_path)

        load_notebook_btn.click()
        time.sleep(20)
        self.driver.switch_to.window(self.driver.window_handles[-1])

        self.download_from_jupyter_notebook_page(download_path=download_path)
        print(f"Downloading jupyter files to {download_path}")
        time.sleep(5)
        close_all_windows_except_main(self.driver)


    def get_course_data(self, url:str):
        """
        Parse data from course and return information about it in python object format.

        Returns
        -------
        dict
            Dict with course data
            {
                'name': str,
                'weeks': [
                    {
                        'name': str,
                        'url': str,
                        'lesson_groups': [
                            {
                                name: str,
                                lessons: [
                                    {
                                        'name': str,
                                        'url': str,
                                        'type': str
                                    },
                                    ...
                                ]
                            },
                            ...
                        ]
                    }, 
                    ...
                ]
            }
        """

        self.driver.get(url)
        WeekPageActions.wait_week_page_loading(self.driver)
    
        course_name = self.driver.find_element(
            By.CSS_SELECTOR, 
            week_page_items_paths["course_name"]
        ).get_attribute("title").strip()

        course_data = {
            "name": course_name,
            "weeks": []
        }

        week_items = self.driver.find_elements(
            By.CSS_SELECTOR, 
            week_page_items_paths["week_items"])

        for week_item in week_items:
            name = week_item.text.strip()
            url = week_item.get_attribute("href")

            week_data = {
                "name": name,
                "url": url,
                "lessons_groups": []
            }
            course_data["weeks"].append(week_data)

        for week in course_data["weeks"]:
            url = week["url"]
            week_data = WeekPageActions.get_week_data(driver=self.driver, url=url)
            week["name"] += f" {week_data['name']}"
            week["lessons_groups"] = week_data["lessons_groups"]
        
        return course_data

    def download_course(self, url:str, download_path:Path):
        if not isinstance(type(download_path), Path):
            download_path = Path(download_path)

        course_data = self.get_course_data(url)
        file_name = prepare_file_name(course_data["name"])
        with open(download_path / f"{file_name}.json", "w", encoding="utf-8") as file:
            json.dump(course_data, file, indent=2)

        self.download_by_course_data(course_data, download_path)
        
    def download_by_course_data(self, course_data:Dict, download_path:Path):
        course_name = prepare_dir_name(course_data["name"])
        for week_index, week_data in enumerate(course_data["weeks"]):
            week_name = prepare_dir_name(week_data["name"])
            print(week_name)

            for group_index, lesson_group_data in enumerate(week_data["lessons_groups"]):
                lesson_lessons_group_items__group_name = f'{group_index+1} {prepare_dir_name(lesson_group_data["name"])}'
                print(f"\t{lesson_lessons_group_items__group_name}")
                
                for lesson_index, lesson_data in enumerate(lesson_group_data["lessons"]):
                    if ALLOW_LESSON_MISSING and not lesson_data["name"]:
                        continue
                    
                    lesson_name = f'{lesson_index+1} {prepare_dir_name(lesson_data["name"])}'
                    lesson_type = lesson_data["type"]
                    lesson_url = lesson_data["url"]
                    lesson_is_locked = lesson_data["is_locked"]
                    lesson_action = lesson_data["action"]
                    lesson_download_path = download_path / course_name / week_name / lesson_lessons_group_items__group_name / lesson_name
                    print(f"\t\t{lesson_name}")

                    make_dirs_if_not_exists(lesson_download_path)

                    assert lesson_action is not None, "Lesson action is None"

                    if lesson_is_locked:
                        continue
                    
                    if lesson_action == "video":
                        VideoPageActions.download(driver=self.driver, url=lesson_url, download_path=lesson_download_path)

                    elif lesson_action == "quiz":
                        QuizPageActions.download(driver=self.driver, url=lesson_url, download_path=lesson_download_path)

                    elif lesson_action == "screenshot" and not lesson_is_locked:
                        ReadingPageActions.download(driver=self.driver, url=lesson_url, download_path=lesson_download_path)

                    elif lesson_action == "code" and not lesson_is_locked:
                        self.download_from_programming_assignment_page(lesson_url, lesson_download_path)

                    elif lesson_is_locked:
                        ReadingPageActions.download(driver=self.driver, url=lesson_url, download_path=lesson_download_path)

                    else:
                        raise Exception(f"Unrecognized lesson action {Fore.YELLOW}{lesson_action}{Fore.RESET}!")
