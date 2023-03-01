import sys
import os
import pathlib
import pickle
import time
import random
import requests
import threading
import json
import argparse

from defines import ROOT_DIR
from defines import DOWNLOAD_PATH
from defines import WEBDRIVER_PATH
from defines import TIMEOUT
from utils import prepare_file_name
from utils import prepare_dir_name
from utils import get_inner_text
from utils import make_dirs_if_not_exists
from utils import repeater
from driver_builder import build_chrome_driver
from bs4 import BeautifulSoup
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException


week_page_items_paths = {
    "course_name": "h2[title]", # h3.cds-137
    # "week_items": ".css-vquajy ul li a",
    "week_items": "nav[aria-label='Course'] div[title='Course Material'] ul li a",
    "lessons_group_items": ".rc-LessonCollectionBody > .rc-ItemGroupLesson",
    "week_name": ".rc-PeriodPageRefresh h1",
    "lessons_group_items__group_name": "h2",
    "downloads_dropdown_menu": "#downloads-dropdown-btn",
    "downloads_dropdown_menu_items": 'ul[role="menu"].bt3-dropdown-menu > li.menuitem > a',
    "file_name": "span",
    "lessons_items": ".cds-AccordionRoot-container > div ul li a",
    "lessons_items__lesson_name": "p[data-test='rc-ItemName']",
    "lessons_items__lesson_type": ".rc-WeekItemAnnotations > div.css-6t2mmp", # class required
    
}

login_page_items_paths = {
    "login_email_field": "form #email",
    "login_password_field": "form #password",
    "login_button_send": "form button[type='submit'][data-e2e='login-form-submit-button']"
}

available_lesson_types = (
    "video", 
    "programming assignment", 
    "practice programming assignment", 
    "quiz", 
    "ungraded external tool", 
    "reading",
    "peer-graded assignment",
    "review your peers"
)


def _download_and_save_file(url, path):
    print(f"GET: {url}")
    response = requests.request("GET", url)
    with open(path, "wb") as file:
        file.write(response.content)
    print(f"Downloaded: {path}")


def _wait_week_page_loading(driver):
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
            week_page_items_paths["lessons_group_items"]
        )
    )

    print("Loading lessons")
    wait.until(
        lambda driver: driver.find_elements(
            By.CSS_SELECTOR,
            week_page_items_paths["lessons_group_items"] + " " + week_page_items_paths["lessons_items"]
        )
    )

    print("Loading lesson type")
    wait.until(
        lambda driver: driver.find_elements(
            By.CSS_SELECTOR, 
            week_page_items_paths["lessons_group_items"] + \
                " " + \
                week_page_items_paths["lessons_items"] + \
                " " + \
                week_page_items_paths["lessons_items__lesson_type"]
        )
    )
    
    time.sleep(3)
    print("Week page loaded")
    print()


def _wait_video_page_loading(driver):
    print("Loading video page")
    time.sleep(2)
    wait = WebDriverWait(driver, TIMEOUT)

    print("Loading download dropdown button")
    wait.until(
        lambda driver: driver.find_element(By.CSS_SELECTOR, week_page_items_paths["downloads_dropdown_menu"])
    )

    time.sleep(1)
    print("Video page loaded")
    print()


def _wait_video_dropdown_menu_loading(driver):
    print("Lading dropdown menu")
    wait = WebDriverWait(driver, TIMEOUT)
    
    print("Loading downloads dropdown menu items")
    dropdown_items = wait.until(
        lambda driver: driver.find_elements(By.CSS_SELECTOR, week_page_items_paths["downloads_dropdown_menu_items"])
    )

    print("Loading file names")
    wait.until(
        lambda driver: len(driver.find_elements(
                By.CSS_SELECTOR, f'{week_page_items_paths["downloads_dropdown_menu_items"]} {week_page_items_paths["file_name"]}:nth-child(1)'
            )) >= len(dropdown_items)
    )
    time.sleep(1)
    print("Dropdown menu loaded")
    print()


def _wait_login_page(driver):
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


class CourseraParser:
    def __init__(self, webdriver=None):
        self.driver = webdriver or build_chrome_driver(
                                        webdriver_path=WEBDRIVER_PATH, 
                                        headless=True, 
                                        tor=False, 
                                        no_logging=True, 
                                        detach=False, 
                                        download_path=DOWNLOAD_PATH)


    def _get_lesson_data(self, lesson_item):
        """
        Gets information about lesson by lesson item
        
        Parameters
        ----------
        lesson_item : selenium.webdriver.remote.webelement.WebElement
            Lesson item. 
            Check path in week_page_items_paths: lessons_group_items + lessons_items.
        

        Returns
        -------
        dict 
            {
                'name': str, # lesson name
                'url': str,  # lesson url
                'type': str  # lesson type (Check available_lesson_types variable)
            }
        """
        lesson_item_bs = BeautifulSoup(lesson_item.get_attribute("outerHTML"), "html.parser").find("a")
        lesson_url = lesson_item_bs["href"]
        lesson_name = lesson_item_bs.select_one(week_page_items_paths["lessons_items__lesson_name"]).get_text().strip()
        lesson_type = get_inner_text(lesson_item_bs.select_one(week_page_items_paths["lessons_items__lesson_type"]))
        
        if lesson_url.startswith("/"):
            lesson_url = "https://www.coursera.org" + lesson_url

        assert lesson_url, "Empty lesson url"
        assert lesson_name, "Empty lesson name"
        assert lesson_type, "Empty lesson type"
        assert lesson_url.startswith("http"), "Invalid url"
        assert lesson_type.lower() in available_lesson_types, \
                f"Unrecognized lesson type {lesson_type}"

        lesson_data = {
            "name": lesson_name,
            "url": lesson_url,
            "type": lesson_type
        }

        return lesson_data

    def _get_lessons_data(self, lessons_block):
        time.sleep(2)
        lessons_items = WebDriverWait(lessons_block, TIMEOUT).until(
            lambda lessons_block: lessons_block.find_elements(By.CSS_SELECTOR, week_page_items_paths["lessons_items"])
        )
        lessons_data = []

        for lesson_index, lesson_item in enumerate(lessons_items):
            lesson_data = self._get_lesson_data(lesson_item)
            
            lessons_data.append(lesson_data)
        
        return lessons_data

    def user_control(self, url=None):
        if url:
            self.driver.get(url)
        
        os.system("pause")

    def save_cookies(self, path):
        with open(path, "wb") as file:
            pickle.dump(self.driver.get_cookies(), file)

    def load_cookies(self, path):
        with open(path, "rb") as file:
            cookies = pickle.load(file)

        for cookie in cookies:
            self.driver.add_cookie(cookie)

    def login_by_cookies(self, path):
        url = "https://www.coursera.org/"
        self.driver.get(url)
        self.load_cookies(path)

    def login_by_site(self, email=None, password=None):
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

    def change_download_path(self, download_path):
        self.driver.command_executor._commands['send_command'] = (
            'POST', '/session/$sessionId/chromium/send_command')

        params = {
            'cmd': 'Page.setDownloadBehavior',
            'params': { 'behavior': 'allow', 'downloadPath': str(download_path) }
        }
        self.driver.execute("send_command", params)

    def _toggle_dropdown_menu(self, css_selector):
        dropdown_btn = self.driver.find_element(By.CSS_SELECTOR, css_selector)
        dropdown_btn.click()

    def _select_subtitles_lang(self, lang, css_selector):
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
    def download_from_video_page(self, url, download_path):
        self.driver.get(url)
        self.change_download_path(download_path)
        _wait_video_page_loading(self.driver)

        if not download_path.exists():
            os.makedirs(download_path)

        self._toggle_dropdown_menu(week_page_items_paths["downloads_dropdown_menu"])

        _wait_video_dropdown_menu_loading(self.driver)
        dropdown_menu_items = self.driver.find_elements(By.CSS_SELECTOR, week_page_items_paths["downloads_dropdown_menu_items"])

        threads = []

        for item in dropdown_menu_items:
            time.sleep(random.random()*2)
            file_name = item.find_element(By.CSS_SELECTOR, week_page_items_paths["file_name"]).text.strip()
            href = item.get_attribute("href")
            
            if href.startswith("/"):
                href = "https://www.coursera.org" + href

            inner_text = item.get_attribute("innerText").strip().lower()
            if "mp4" in inner_text:
                file_type = "mp4"
            elif "vtt" in inner_text:
                file_type = "vtt"
            elif "txt" in inner_text:
                file_type = "txt"
            elif "doc" in inner_text:
                file_type = "doc"
            elif "pdf" in inner_text:
                file_type = "pdf"
            elif "pptx" in inner_text:
                file_type = "pptx"
            else:
                raise Exception(f"Invalid file type \n{inner_text}")

            file_name = prepare_file_name(file_name)
            assert href.startswith("https://") or href.startswith("http://"), f"Invalid url {href}" 

            downloading_thread = threading.Thread(target=_download_and_save_file, kwargs={
                "url": href,
                "path": download_path / f"{file_name}.{file_type}"
            })
            
            threads.append(downloading_thread)
            downloading_thread.start()

        for thread in threads:
            thread.join()

    def get_week_data(self, url):
        print(f"Get week data")
        print(f"URL: {url}")
        print()

        self.driver.get(url)

        _wait_week_page_loading(self.driver)

        lessons_group_items = self.driver.find_elements(
            By.CSS_SELECTOR, 
            week_page_items_paths["lessons_group_items"])

        week_name = self.driver.find_element(
            By.CSS_SELECTOR, 
            week_page_items_paths["week_name"]).text.strip()

        week_data = {
            "name": week_name,
            "lessons_groups": []
        }

        for group_index, lessons_group in enumerate(lessons_group_items):
            lessons_group_items__group_name = lessons_group.find_element(By.CSS_SELECTOR, week_page_items_paths["lessons_group_items__group_name"]).text.strip()
            lessons_data = self._get_lessons_data(lessons_group)

            group_data = {
                "name": lessons_group_items__group_name,
                "lessons": lessons_data
            }
            week_data["lessons_groups"].append(group_data)
        
        return week_data     

    def get_course_data(self, url):
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

    def download_course(self, url, download_path):
        if not isinstance(type(download_path), pathlib.Path):
            download_path = pathlib.Path(download_path)

        course_data = self.get_course_data(url)
        file_name = prepare_file_name(course_data["name"])
        with open(download_path / f"{file_name}.json", "w", encoding="utf-8") as file:
            json.dump(course_data, file, indent=2)

        self.download_by_course_data(course_data, download_path)
        
    def download_by_course_data(self, course_data, download_path):
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
                    video_download_path = download_path / course_name / week_name / lesson_lessons_group_items__group_name / lesson_name
                    print(f"\t\t{lesson_name}")

                    make_dirs_if_not_exists(video_download_path)
                    
                    if lesson_type.lower() == "video":
                        self.download_from_video_page(lesson_url, video_download_path)
