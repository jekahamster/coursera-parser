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
from selenium.common.exceptions import NoSuchElementException
from colorama import Fore
from datetime import datetime

from typing import Union
from typing import List
from typing import Dict


colorama.init(autoreset=True)

week_page_items_paths = {
    "course_name": "h2[title]", # h3.cds-137
    # "week_items": ".css-vquajy ul li a",
    "week_name": ".rc-PeriodPageRefresh .cds-AccordionRoot-standard > h2",
    
    "week_items": "nav[aria-label='Course'] .cds-AccordionRoot-container.cds-AccordionRoot-silent ul li a[data-test='rc-WeekNavigationItem']", # Left side bar with all weeks
    
    "lessons_groups": ".rc-LessonCollectionBody > .rc-ItemGroupLesson",
    "lessons_groups__name": "h2 .cds-AccordionHeader-content .cds-AccordionHeader-labelGroup > span",
    "lessons_groups__lessons": ".cds-AccordionRoot-container > div ul li",
    "lessons_groups__lessons__link": "li > div > a",
    "lessons_groups__lessons__name": "p[data-test='rc-ItemName']",
    "lessons_groups__lessons__type": ".rc-WeekItemAnnotations > div:has(.rc-EffortText)",
    "lessons_groups__lessons__type_class": "li > div",
    "lessons_groups__lessons__hidden_item": ".locked-tooltip" # TODO: No element found
   
}

quiz_page_items_paths = {
    "open_quiz_button": "#main div[data-e2e='CoverPageRow__right-side-view'] button",
    "exit_quiz_button": "div[data-classname='tunnelvision-window-0'] .rc-TunnelVisionClose",
    "scrolling_element": "#TUNNELVISIONWRAPPER_CONTENT_ID",
    "honor_code_accept_btn": ".cds-Dialog-dialog .align-right .cds-button-disableElevation"
}

reading_page_items_paths = {
    "scrolling_element": "#main-container",
    # "left_side_bar": "div:has(> #main-container) > div:nth-child(1)",
    "coursera_bot_chat_button": "#coursera-coach-widget",
    "header_container": "#header-container",
    "close_menu": "div:has(> #main-container) > div:nth-child(1) button[data-track-component='focused_lex_nav_close_button']",
    "open_menu": "#main-container button[data-track-component='focused_lex_nav_open_button']"
}

video_page_items_paths = {
    "downloads_tab_button": "button[id$='DOWNLOADS']",
    "files_links": "a[download]",
    "video_name": "h1.video-name",
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



lesson_type2action = {
    "": "screenshot",
    "video": "video",
    "programming assignment": "code",
    "practice programming assignment": "code",
    "quiz": "quiz",
    "ungraded external tool": None, # ?
    "reading": "screenshot",
    "peer-graded assignment": None,
    "review your peers": None,
    "Discussion Prompt": "screenshot",
    "Practice Quiz": "quiz",
    "Graded External Tool": None,
    "Ungraded Plugin": "screenshot", # (youtube link) https://www.coursera.org/learn/differential-equations-engineers/ungradedWidget/NLLHm/defining-the-exponential-logarithm-sine-and-cosine-functions-using-odes
    "Ungraded App Item": "screenshot", # https://www.coursera.org/learn/machine-learning-probability-and-statistics/home/week/1
    "Lab": "code", 
    "Graded App Item": None,
    "Guided Project": None,
    "Practice Assignment": "code",
    "Graded Assignment": "quiz"
}

lesson_type_class2action = {
    "WeekSingleItemDisplay-lecture": "video",
    "WeekSingleItemDisplay-supplement": "screenshot",
    "WeekSingleItemDisplay-discussionPrompt": None,
    "WeekSingleItemDisplay-exam": "quiz",
    "WeekSingleItemDisplay-ungradedWidget": "screenshot", # Ungraded Plugin
    "WeekSingleItemDisplay-ungradedLti": "screenshot", # Ungraded App Item
    "WeekSingleItemDisplay-ungradedLab": "code",
    "WeekSingleItemDisplay-quiz": "quiz",
    "WeekSingleItemDisplay-gradedProgramming": "code",
    "WeekSingleItemDisplay-ungradedProgramming": None,
    "WeekSingleItemDisplay-gradedLti": None,
    "WeekSingleItemDisplay-ungradedAssignment": "code", # Practice Assignment 
    "WeekSingleItemDisplay-staffGraded": "quiz" # Graded Assignment
}

lesson_type2action = {k.lower() : v for k, v in lesson_type2action.items()}
lesson_type_class2action = {k.lower() : v for k, v in lesson_type_class2action.items()}


def _download_and_save_file(url:str, path:Union[str, Path]):
    print(f"GET: {url}")
    try:
        response = requests.request("GET", url)
        with open(path, "wb") as file:
            file.write(response.content)
        print(f"{Fore.GREEN}Downloaded{Fore.RESET}: {path}")
    except Exception as e:
        print(Fore.RED + str(e))
        print(traceback.format_exc())
        exit()


def _wait_week_page_loading(driver:BaseWebDriver):
    global week_page_items_paths
    
    print("Loading week page")
    wait = WebDriverWait(driver, TIMEOUT)

    print("Loading week items")
    wait.until(
        lambda driver: driver.find_elements(
            By.CSS_SELECTOR, 
            week_page_items_paths["week_items"]
        )
    )
    
    print("Loading week name")
    wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR, 
            week_page_items_paths["week_name"]
        )
    )

    print("Loading lessons groups")
    wait.until(
        lambda driver: driver.find_elements(
            By.CSS_SELECTOR, 
            week_page_items_paths["lessons_groups"]
        )
    )

    print("Loading lessons")
    wait.until(
        lambda driver: driver.find_elements(
            By.CSS_SELECTOR,
            week_page_items_paths["lessons_groups"] + " " + week_page_items_paths["lessons_groups__lessons"]
        )
    )

    print("Loading lesson type")
    wait.until(
        lambda driver: driver.find_elements(
            By.CSS_SELECTOR, 
            week_page_items_paths["lessons_groups"] + \
                " " + \
                week_page_items_paths["lessons_groups__lessons"] + \
                " " + \
                week_page_items_paths["lessons_groups__lessons__type"]
        )
    )
    
    time.sleep(3)
    print("Week page loaded")
    print()


def _wait_video_page_loading(driver:BaseWebDriver):
    print("Loading video page")
    time.sleep(2)
    wait = WebDriverWait(driver, TIMEOUT)

    print("Loading downloads tab button")
    downloads_tab_btn = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            video_page_items_paths["downloads_tab_button"]
        )
    )

    print("Loading video name")
    video_name_item = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            video_page_items_paths["video_name"]
        )
    )

    print("Video page loaded")
    
    return downloads_tab_btn, video_name_item


def _wait_video_downloads_tab_loading(driver:BaseWebDriver):
    print("Loading video downloads tab")
    wait = WebDriverWait(driver, TIMEOUT)

    print("Loading files links")
    files_links_items = wait.until(
        lambda driver: driver.find_elements(
            By.CSS_SELECTOR,
            video_page_items_paths["files_links"]
        )
    )

    print("Video downloads tab loaded")
    return files_links_items


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


def _wait_reading_page(driver:BaseWebDriver):
    print("Loading reading page items")
    wait = WebDriverWait(driver, TIMEOUT)

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
    close_menu_btn = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            reading_page_items_paths["close_menu"]
        )
    )

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


def _wait_quiz_page_before_quiz_starting(driver:BaseWebDriver):
    print("Loading quiz page items")
    wait = WebDriverWait(driver, TIMEOUT)

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

    def _get_lesson_data(self, lesson_item:WebElement):
        """
        Gets information about lesson by lesson item
        
        Parameters
        ----------
        lesson_item : selenium.webdriver.remote.webelement.WebElement
            Lesson item. 
            Check path in week_page_items_paths: lessons_groups + lessons_items.
        

        Returns
        -------
        dict 
            {
                'name': str, # lesson name
                'url': str,  # lesson url
                'type': str  # lesson type (Check available_lesson_types variable)
            }
        """
        lesson_item_bs = BeautifulSoup(lesson_item.get_attribute("outerHTML"), "html.parser")
        lesson_url = lesson_item_bs.select_one(week_page_items_paths["lessons_groups__lessons__link"])["href"].strip()
        lesson_name = lesson_item_bs.select_one(week_page_items_paths["lessons_groups__lessons__name"]).get_text().strip()
        lesson_type_class = lesson_item_bs.select_one(week_page_items_paths["lessons_groups__lessons__type_class"])["data-test"]
        
        lesson_type_item = lesson_item_bs.select_one(week_page_items_paths["lessons_groups__lessons__type"])
        if not lesson_type_item:
            warnings.warn(f"Empty lesson_type at lesson '{lesson_name}'")

        lesson_type = get_inner_text(lesson_type_item) if lesson_type_item else ""
        lesson_type_descr = lesson_type_item.text if lesson_type_item else ""

        lesson_action = lesson_type2action[lesson_type.lower()]
        lesson_action_recheck = lesson_type_class2action[lesson_type_class.lower()]

        if lesson_url.startswith("/"):
            lesson_url = "https://www.coursera.org" + lesson_url

        assert lesson_action is not None, f"Lesson action for {lesson_type} is None"
        assert lesson_action == lesson_action_recheck, \
            f"Lesson type {lesson_type} with action {lesson_action} and lesson type class {lesson_type_class} with action {lesson_action_recheck} are not match."
        assert lesson_url, "Empty lesson url"
        assert lesson_name, "Empty lesson name"
        assert lesson_url.startswith("http"), "Invalid url"
        assert (DEBUG and lesson_type.lower() in lesson_type2action.keys()) or not DEBUG, \
                f"Unrecognized lesson type {lesson_type}. Set DEBUG = False in defines.py to disable this."
        assert (DEBUG and lesson_type_class.lower() in lesson_type_class2action.keys()) or not DEBUG, \
                f"Unrecognized lesson type class {lesson_type_class}. Set DEBUG = False in defines.py to disable this."

        try:
            lesson_item.find_element(By.CSS_SELECTOR, week_page_items_paths["lessons_groups__lessons__hidden_item"])
            is_locked = True
        except NoSuchElementException:
            is_locked = False

        lesson_data = {
            "name": lesson_name,
            "url": lesson_url,
            "type": lesson_type,
            "type_descr": lesson_type_descr,
            "type_class": lesson_type_class,
            "action": lesson_action,
            "is_locked": is_locked
        }

        return lesson_data

    def _get_lessons_data(self, lessons_block:WebElement):
        time.sleep(2)

        lessons_items = WebDriverWait(lessons_block, TIMEOUT).until(
            lambda lessons_block: lessons_block.find_elements(By.CSS_SELECTOR, week_page_items_paths["lessons_groups__lessons"])
        )
        lessons_data = []

        for lesson_index, lesson_item in enumerate(lessons_items):
            try:
                lesson_data = self._get_lesson_data(lesson_item)
            except TypeError as e:
                print(Fore.RED + f"{e} was occured while getting lesson data!")
                if not ALLOW_LESSON_MISSING:
                    print(traceback.format_exc())
                    raise e
                
                lesson_data = {
                    "name": "",
                    "url": "",
                    "type": "",
                    "type_descr": "",
                    "type_class": "",
                    "is_locked": ""
                }
            except AssertionError as e:
                print(traceback.format_exc())
                print(f"Lesson index: {lesson_index}")
                raise e

            lessons_data.append(lesson_data)

        
        return lessons_data

    def _get_file_name_from_video_link_item(self, item:WebElement):
        original_file_name = item.get_attribute("download").strip()
        suffix = Path(original_file_name).suffix
        
        link_title = item.text.strip()
        link_title_suffix = link_title.rfind(" ")
        file_name_stem = link_title[:link_title_suffix]

        if not suffix:
            suffix = "." + link_title[link_title_suffix + 1:].strip()

        if suffix == "WebVTT":
            suffix = ".vtt"

        file_name = f"{file_name_stem}{suffix}"
        return file_name

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
    def download_from_quiz_page(self, url:str, download_path:Path):
        self.driver.get(url)
        start_quiz_btn = _wait_quiz_page_before_quiz_starting(self.driver)

        try:
            honor_code_btn = self.driver.find_element(By.CSS_SELECTOR, quiz_page_items_paths["honor_code_accept_btn"])
            honor_code_btn.click()
        except NoSuchElementException:
            pass

        start_quiz_btn.click()
        time.sleep(1)

        exit_quiz_btn, scrolling_element = _wait_quiz_page_after_quiz_starting(self.driver)
        time.sleep(5)

        image_name = f"quiz_screenshot.png"

        fullpage_screenshot(
            self.driver, 
            scrolling_element=scrolling_element,
            file=download_path / image_name,
            time_delay=2)
        
        exit_quiz_btn.click()

    @repeater(TIMEOUT)
    def download_from_reading_page(self, url:str = None, download_path:Path = None):
        # if url is not specified then processcurrent page
        
        assert download_path, "Download path is not specified"

        if url:
            self.driver.get(url)
        
        time.sleep(5)
        scrolling_element, header_container, close_menu_btn, open_menu_btn, coursera_bot_chat_button = _wait_reading_page(self.driver)
        
        if not open_menu_btn:
            close_menu_btn.click()

        pdf_name = f"reading_page.pdf"
        image_name = f"reading_screenshot.png"

        base64code = self.driver.print_page()
        with open(download_path / pdf_name, "wb") as file:
            file.write(base64.b64decode(base64code))

        fullpage_screenshot(
            self.driver, 
            scrolling_element=scrolling_element,
            removing_elements=filter(lambda x: x is not None, [header_container, coursera_bot_chat_button]),
            file=download_path / image_name)

    @repeater(TIMEOUT)
    def download_from_video_page(self, url:str, download_path:Path):
        self.driver.get(url)
        
        downloads_tab_btn, video_name_item = _wait_video_page_loading(self.driver)

        if not download_path.exists():
            os.makedirs(download_path)

        downloads_tab_btn.click()
        time.sleep(1)
        
        files_links_items = _wait_video_downloads_tab_loading(self.driver)
        threads = []

        for item in files_links_items:
            time.sleep(random.random()*2)

            file_name = self._get_file_name_from_video_link_item(item)

            file_name = prepare_file_name(file_name)
            href = item.get_attribute("href")

            assert href.startswith("https://") or href.startswith("http://"), f"Invalid url {href}" 

            downloading_thread = threading.Thread(target=_download_and_save_file, kwargs={
                "url": href,
                "path": download_path / file_name
            })
            
            threads.append(downloading_thread)
            downloading_thread.start()

        for thread in threads:
            thread.join()

        video_name = video_name_item.text.strip()
        with open(download_path / f"video_name.txt", "w", encoding="UTF-8") as file:
            file.write(video_name)

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

    @repeater(TIMEOUT)
    def get_week_data(self, url:str):
        print(f"Get week data")
        print(f"URL: {url}")
        print()

        self.driver.get(url)

        _wait_week_page_loading(self.driver)

        lessons_groups = self.driver.find_elements(
            By.CSS_SELECTOR, 
            week_page_items_paths["lessons_groups"])

        week_name = self.driver.find_element(
            By.CSS_SELECTOR, 
            week_page_items_paths["week_name"]).text.strip()

        week_data = {
            "name": week_name,
            "lessons_groups": []
        }

        for group_index, lessons_group in enumerate(lessons_groups):
            lessons_groups__name = lessons_group.find_element(By.CSS_SELECTOR, week_page_items_paths["lessons_groups__name"]).text.strip()
            
            try:
                lessons_data = self._get_lessons_data(lessons_group)
            except AssertionError as e:
                print(f"Group index: {group_index}")
                print(f"Group name: {lessons_groups__name}")
                raise e

            group_data = {
                "name": lessons_groups__name,
                "lessons": lessons_data
            }
            week_data["lessons_groups"].append(group_data)
        
        return week_data     

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
        _wait_week_page_loading(self.driver)
    
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
            week_data = self.get_week_data(url)
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

                    if lesson_action == "video" and not lesson_is_locked:
                        self.download_from_video_page(lesson_url, lesson_download_path)

                    elif lesson_action == "quiz":
                        self.download_from_quiz_page(lesson_url, lesson_download_path)

                    elif lesson_action == "screenshot" and not lesson_is_locked:
                        self.download_from_reading_page(lesson_url, lesson_download_path)

                    elif lesson_action == "code" and not lesson_is_locked:
                        self.download_from_programming_assignment_page(lesson_url, lesson_download_path)

                    elif lesson_is_locked:
                        self.download_from_reading_page(lesson_url, lesson_download_path)

                    else:
                        raise Exception(f"Unrecognized lesson action {Fore.YELLOW}{lesson_action}{Fore.RESET}!")
