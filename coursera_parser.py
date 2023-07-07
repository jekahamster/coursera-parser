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

from pathlib import Path
from defines import ROOT_DIR
from defines import DOWNLOAD_PATH
from defines import WEBDRIVER_PATH
from defines import TIMEOUT
from defines import DEBUG
from utils import prepare_file_name
from utils import prepare_dir_name
from utils import get_inner_text
from utils import make_dirs_if_not_exists
from utils import repeater
from utils import fullpage_screenshot
from driver_builder import build_chrome_driver
from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException
from colorama import Fore
from datetime import datetime

from typing import Union
from typing import List
from typing import Dict


colorama.init(autoreset=True)

week_page_items_paths = {
    "course_name": "h2[title]", # h3.cds-137
    # "week_items": ".css-vquajy ul li a",
    "week_name": ".rc-PeriodPageRefresh h1",
    
    "week_items": "nav[aria-label='Course'] div[title='Course Material'] ul li a",
    
    "lessons_groups": ".rc-LessonCollectionBody > .rc-ItemGroupLesson",
    "lessons_groups__name": "h2",
    "lessons_groups__lessons": ".cds-AccordionRoot-container > div ul li",
    "lessons_groups__lessons__link": "li > div > a",
    "lessons_groups__lessons__name": "p[data-test='rc-ItemName']",
    "lessons_groups__lessons__type": ".rc-WeekItemAnnotations > div.css-6t2mmp", # ! css class required !
    "lessons_groups__lessons__type_class": "li > div"
   
}

quiz_page_items_paths = {
    "open_quiz_button": "#main div[data-e2e='CoverPageRow__right-side-view'] button",
    "exit_quiz_button": "div[data-classname='tunnelvision-window-0'] .rc-TunnelVisionClose",
    "scrolling_element": "#TUNNELVISIONWRAPPER_CONTENT_ID",
    "honor_code_accept_btn": ".cds-Dialog-dialog .align-right .cds-button-disableElevation"
}

reading_page_items_paths = {
    "scrolling_element": ".ItemPageLayout_content_body",
    "left_side_bar": ".ItemPageLayout_content_navigation.cds-grid-item",
    "coursera_bot_chat_button": "#chat-button-container"
}

video_page_items_paths = {
    "downloads_dropdown_menu_button": "#downloads-dropdown-btn",
    "downloads_dropdown_menu_items": 'ul[role="menu"].bt3-dropdown-menu > li.menuitem > a',
    "file_name": "span",
    "video_name": "h1.video-name"
}

login_page_items_paths = {
    "login_email_field": "form #email",
    "login_password_field": "form #password",
    "login_button_send": "form button[type='submit'][data-e2e='login-form-submit-button']"
}

available_lesson_types = list(map(lambda x: x.lower(), [
    "",
    "video", 
    "programming assignment", 
    "practice programming assignment", 
    "quiz", 
    "ungraded external tool", 
    "reading",
    "peer-graded assignment",
    "review your peers",
    "Discussion Prompt",
    "Practice Quiz",
    "Graded External Tool",
    "Ungraded Plugin"
]))

available_lesson_type_classes = list(map(lambda x: x.lower(), [
    "WeekSingleItemDisplay-lecture",
    "WeekSingleItemDisplay-supplement",
    "WeekSingleItemDisplay-lecture",
    "WeekSingleItemDisplay-discussionPrompt",
    "WeekSingleItemDisplay-exam",
    "WeekSingleItemDisplay-ungradedWidget"
]))



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

    print("Loading download dropdown button")
    wait.until(
        lambda driver: driver.find_element(By.CSS_SELECTOR, video_page_items_paths["downloads_dropdown_menu_button"])
    )

    time.sleep(1)
    print("Video page loaded")
    print()


def _wait_video_dropdown_menu_loading(driver:BaseWebDriver):
    print("Lading dropdown menu")
    wait = WebDriverWait(driver, TIMEOUT)
    
    print("Loading downloads dropdown menu items")
    dropdown_items = wait.until(
        lambda driver: driver.find_elements(By.CSS_SELECTOR, video_page_items_paths["downloads_dropdown_menu_items"])
    )

    print("Loading file names")
    wait.until(
        lambda driver: len(driver.find_elements(
                By.CSS_SELECTOR, f'{video_page_items_paths["downloads_dropdown_menu_items"]} {video_page_items_paths["file_name"]}:nth-child(1)'
            )) >= len(dropdown_items)
    )
    time.sleep(1)
    print("Dropdown menu loaded")
    print()


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

    print("Loading left side bar")
    left_side_bar = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            reading_page_items_paths["left_side_bar"]
        ) 
    )

    print("Loading coursera bot chat button")
    coursera_bot_chat_button = wait.until(
        lambda driver: driver.find_element(
            By.CSS_SELECTOR,
            reading_page_items_paths["coursera_bot_chat_button"]
        ) 
    )

    print("Reading page loaded")
    return scrolling_element, left_side_bar, coursera_bot_chat_button


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


        if lesson_url.startswith("/"):
            lesson_url = "https://www.coursera.org" + lesson_url

        assert lesson_url, "Empty lesson url"
        assert lesson_name, "Empty lesson name"
        assert lesson_url.startswith("http"), "Invalid url"
        assert (DEBUG and lesson_type.lower() in available_lesson_types) or not DEBUG, \
                f"Unrecognized lesson type {lesson_type}. Set DEBUG = False in defines.py to disable this."
        assert (DEBUG and lesson_type_class.lower() in available_lesson_type_classes) or not DEBUG, \
                f"Unrecognized lesson type class {lesson_type_class}. Set DEBUG = False in defines.py to disable this."

        lesson_data = {
            "name": lesson_name,
            "url": lesson_url,
            "type": lesson_type,
            "type_descr": lesson_type_descr,
            "type_class": lesson_type_class
        }

        return lesson_data

    def _get_lessons_data(self, lessons_block:WebElement):
        time.sleep(2)

        lessons_items = WebDriverWait(lessons_block, TIMEOUT).until(
            lambda lessons_block: lessons_block.find_elements(By.CSS_SELECTOR, week_page_items_paths["lessons_groups__lessons"])
        )
        lessons_data = []

        for lesson_index, lesson_item in enumerate(lessons_items):
            lesson_data = self._get_lesson_data(lesson_item)
            
            lessons_data.append(lesson_data)
        
        return lessons_data

    def _get_file_name_from_video_dropdown_item(self, item:WebElement):
        original_file_name = item.get_attribute("download").strip()
        point_index = original_file_name[::-1].find(".")
        suffix = original_file_name[-point_index-1:]
        file_name = item.find_elements(By.CSS_SELECTOR, "span")[0].text.strip()
        
        return f"{file_name}{suffix}"

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

        honor_code_btn = self.driver.find_element(By.CSS_SELECTOR, quiz_page_items_paths["honor_code_accept_btn"])
        if honor_code_btn:
            honor_code_btn.click()

        start_quiz_btn.click()
        time.sleep(1)

        exit_quiz_btn, scrolling_element = _wait_quiz_page_after_quiz_starting(self.driver)
        time.sleep(5)

        str_date = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        image_name = f"screenshot_{str_date}.png"

        fullpage_screenshot(
            self.driver, 
            scrolling_element=scrolling_element,
            file=download_path / image_name,
            time_delay=2)
        
        exit_quiz_btn.click()

    @repeater(TIMEOUT)
    def download_from_reading_page(self, url:str, download_path:Path):
        self.driver.get(url)
        time.sleep(5)
        scrolling_element, left_side_bar, coursera_chat_bot_btn = _wait_reading_page(self.driver)

        str_date = datetime.now().strftime('%d-%m-%Y_%H-%M-%S')
        pdf_name = f"page_{str_date}.pdf"
        image_name = f"screenshot_{str_date}.png"

        base64code = self.driver.print_page()
        with open(download_path / pdf_name, "wb") as file:
            file.write(base64.b64decode(base64code))

        fullpage_screenshot(
            self.driver, 
            scrolling_element=scrolling_element,
            removing_elements=[coursera_chat_bot_btn],
            # removing_elements=[left_side_bar, coursera_chat_bot_btn]
            file=download_path / image_name)

    @repeater(TIMEOUT)
    def download_from_video_page(self, url:str, download_path:Path):
        self.driver.get(url)
        self.change_download_path(download_path)
        _wait_video_page_loading(self.driver)

        if not download_path.exists():
            os.makedirs(download_path)

        self._toggle_dropdown_menu(video_page_items_paths["downloads_dropdown_menu_button"])

        _wait_video_dropdown_menu_loading(self.driver)
        dropdown_menu_items = self.driver.find_elements(By.CSS_SELECTOR, video_page_items_paths["downloads_dropdown_menu_items"])
        threads = []

        for item in dropdown_menu_items:
            time.sleep(random.random()*2)

            file_name = self._get_file_name_from_video_dropdown_item(item)
            file_name = prepare_file_name(file_name)
            href = item.get_attribute("href")
            
            if href.startswith("/"):
                href = "https://www.coursera.org" + href

            assert href.startswith("https://") or href.startswith("http://"), f"Invalid url {href}" 

            downloading_thread = threading.Thread(target=_download_and_save_file, kwargs={
                "url": href,
                "path": download_path / file_name
            })
            
            threads.append(downloading_thread)
            downloading_thread.start()

        for thread in threads:
            thread.join()

        video_name = self.driver.find_element(By.CSS_SELECTOR, video_page_items_paths["video_name"]).text.strip()
        with open(download_path / f"video_name.txt", "w", encoding="UTF-8") as file:
            file.write(video_name)

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
            lessons_data = self._get_lessons_data(lessons_group)

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
                    lesson_name = f'{lesson_index+1} {prepare_dir_name(lesson_data["name"])}'
                    lesson_type = lesson_data["type"]
                    lesson_url = lesson_data["url"]
                    lesson_download_path = download_path / course_name / week_name / lesson_lessons_group_items__group_name / lesson_name
                    print(f"\t\t{lesson_name}")

                    make_dirs_if_not_exists(lesson_download_path)
                    
                    if lesson_type.lower() == "video":
                        self.download_from_video_page(lesson_url, lesson_download_path)
                    
                    elif lesson_type.lower() == "quiz":
                        self.download_from_quiz_page(lesson_url, lesson_download_path)

                    else:
                        self.download_from_reading_page(lesson_url, lesson_download_path)
