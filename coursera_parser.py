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

from command_parser import CommandParserBuilder
from defines import ROOT_DIR
from defines import DOWNLOAD_PATH
from functools import reduce
from selenium import webdriver 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, StaleElementReferenceException


items_paths = {
    "course_name": ".css-4l66rl h3.cds-137",
    # "week_items": ".css-vquajy ul li a",
    "week_items": "nav[aria-label='Course'] div[title='Course Material'] ul li a",
    "lessons_group_items": ".rc-LessonCollectionBody > .rc-ItemGroupLesson",
    "week_name": "h3.css-1wkjz26 .cds-134 .cds-AccordionHeader-content span.cds-137",
    "group_name": "h3 .cds-137",
    "lessons_ul_item": ".cds-AccordionRoot-container > div ul",
    "downloads_dropdown_menu": "#downloads-dropdown-btn",
    "downloads_dropdown_menu_items": 'ul[role="menu"].bt3-dropdown-menu > li.menuitem > a',
    "file_name": "span",
    "lessons_items": "li a",
    "lesson_name": "p",
    "lesson_type": ".rc-WeekItemAnnotations .css-6t2mmp",   
}

def repeater(function):
    def wrapper(*args, **kwargs):
        while True:
            try:
                return function(*args, **kwargs)
            except (NoSuchElementException, StaleElementReferenceException, WebDriverException) as e:
                print(f"{e.__class__.__name__}: {e}")
            time.sleep(random.random() * 5)

    return wrapper


def _download_and_save_file(url, path):
    print(f"GET: {url}")
    response = requests.request("GET", url)
    with open(path, "wb") as file:
        file.write(response.content)
    print(f"Downloaded: {path}")


def _prepare_name(file_name):
    to_replace = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
    for symbol in to_replace:
        file_name = file_name.replace(symbol, "")  
    return file_name


def _prepare_dir_name(dir_name):
    dir_name = _prepare_name(dir_name)
    if len(dir_name) > 30:
        dir_name = f"{dir_name[:30]}"

    to_replace = ["."]
    for symbol in to_replace:
        dir_name = dir_name.replace(symbol, "")  
    return dir_name

    

def _wait_week_page_loading(driver):
    global items_paths
    print("Wait week page loading")
    wait = WebDriverWait(driver, 300)

    print("lesson type")
    wait.until(
        lambda driver: driver.find_element(By.CSS_SELECTOR, items_paths["lesson_type"])
    )

    print("lessons group items")
    wait.until(
        lambda driver: driver.find_elements(By.CSS_SELECTOR, items_paths["lessons_group_items"])
    )

    # print()
    # wait.until(
    #     lambda driver: driver.find_element(By.CSS_SELECTOR, ".cds-AccordionRoot-container > h3")
    # )

    print("lesson_types")
    wait.until(
        lambda driver: driver.find_elements(By.CSS_SELECTOR, f'{items_paths["lessons_group_items"]} ' \
            f'{items_paths["lessons_ul_item"]} {items_paths["lessons_items"]} {items_paths["lesson_type"]}')
    )

    print("week items")
    wait.until(
        lambda driver: driver.find_element(By.CSS_SELECTOR, items_paths["week_items"])
    )
    
    print("week name")
    wait.until(
        lambda driver: driver.find_element(By.CSS_SELECTOR, items_paths["week_name"])
    )
    
    time.sleep(3)
    print("Page loaded")
    print()


def _wait_video_page_loading(driver):
    print("Wait video page loading")
    time.sleep(2)
    wait = WebDriverWait(driver, 200)

    print("download dropdown button")
    wait.until(
        lambda driver: driver.find_element(By.CSS_SELECTOR, items_paths["downloads_dropdown_menu"])
    )

    time.sleep(1)
    print("Video page loaded")
    print()


def _wait_video_dropdown_menu_loading(driver):
    print("Wait dropdown menu loading")
    wait = WebDriverWait(driver, 300)
    
    print("downloads dropdown menu items")
    dropdown_items = wait.until(
        lambda driver: driver.find_elements(By.CSS_SELECTOR, items_paths["downloads_dropdown_menu_items"])
    )

    print("file names")
    wait.until(
        lambda driver: len(driver.find_elements(
                By.CSS_SELECTOR, f'{items_paths["downloads_dropdown_menu_items"]} {items_paths["file_name"]}:nth-child(1)'
            )) >= len(dropdown_items)
    )
    time.sleep(1)
    print("Dropdown menu loaded")
    print()


class CourseraParser:
    def __init__(self, headless=False):
        self.service = webdriver.chrome.service.Service(executable_path=str(ROOT_DIR / "webdrivers" / "chromedriver.exe"))
        self.chrome_options = webdriver.chrome.options.Options()
        
        if headless:
            self.chrome_options.add_argument("--headless")
        
        prefs = {
            "profile.default_content_setting_values.automatic_downloads": 1,
            "download.default_directory": str(DOWNLOAD_PATH)   
        }
        self.chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome Beta\\Application\\chrome.exe"
        self.chrome_options.add_experimental_option("prefs", prefs)
        self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)

    def __del__(self):
        self.driver.quit()

    def _get_lessons_data(self, lessons_block):
        time.sleep(2)
        lessons_items = WebDriverWait(lessons_block, 60).until(
            lambda lessons_block: lessons_block.find_elements(By.CSS_SELECTOR, items_paths["lessons_items"])
        )
        lessons = []

        for lesson_item in lessons_items:
            lesson_url = lesson_item.get_attribute("href")
            lesson_name = lesson_item.find_element(By.CSS_SELECTOR, items_paths["lesson_name"]).text.strip()
            lesson_type = lesson_item.find_element(By.CSS_SELECTOR, items_paths["lesson_type"]).text.strip()
            
            separator_index = lesson_type.find("•")
            separator_index = separator_index if separator_index != -1 else len(lesson_type)
            lesson_type = lesson_type[:separator_index].strip()

            if lesson_url.startswith("/"):
                lesson_url = "https://www.coursera.org" + lesson_url

            assert lesson_url.startswith("http"), "Invalid url"
            assert lesson_type.lower() in ("video", "programming assignment", "practice programming assignment", 
                            "quiz", "ungraded external tool", "reading"), f"Unrecognized lesson type {lesson_type}"

            lesson_data = {
                "name": lesson_name,
                "url": lesson_url,
                "type": lesson_type
            }
            
            lessons.append(lesson_data)
        
        return lessons

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

    def login(self, path):
        url = "https://www.coursera.org/"
        self.driver.get(url)
        self.load_cookies(path)

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

    @repeater
    def download_from_video_page(self, url, download_path):
        self.driver.get(url)
        self.change_download_path(download_path)
        _wait_video_page_loading(self.driver)

        if not download_path.exists():
            os.makedirs(download_path)

        self._toggle_dropdown_menu(items_paths["downloads_dropdown_menu"])

        _wait_video_dropdown_menu_loading(self.driver)
        dropdown_menu_items = self.driver.find_elements(By.CSS_SELECTOR, items_paths["downloads_dropdown_menu_items"])

        threads = []

        for item in dropdown_menu_items:
            time.sleep(random.random()*2)
            file_name = item.find_element(By.CSS_SELECTOR, items_paths["file_name"]).text.strip()
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

            file_name = _prepare_name(file_name)
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

        lessons_group_items = self.driver.find_elements(By.CSS_SELECTOR, items_paths["lessons_group_items"])

        week_name = self.driver.find_element(By.CSS_SELECTOR, items_paths["week_name"]).text.strip()

        week_data = {
            "name": week_name,
            "lessons_groups": []
        }

        for lesson_group in lessons_group_items:
            group_name = lesson_group.find_element(By.CSS_SELECTOR, items_paths["group_name"]).text.strip()
            lessons_ul_item = lesson_group.find_element(By.CSS_SELECTOR, items_paths["lessons_ul_item"])
            lessons_data = self._get_lessons_data(lessons_ul_item)

            group_data = {
                "name": group_name,
                "lessons": lessons_data
            }
            week_data["lessons_groups"].append(group_data)
        
        return week_data     

    def get_course_data(self, url):
        self.driver.get(url)
        _wait_week_page_loading(self.driver)
    
        course_name = self.driver.find_element(By.CSS_SELECTOR, items_paths["course_name"]).text.strip()
        course_data = {
            "name": course_name,
            "weeks": []
        }

        week_items = self.driver.find_elements(By.CSS_SELECTOR, items_paths["week_items"])        
        for week_item in week_items:
            name = week_item.text.strip()
            url = week_item.get_attribute("href")

            week_data = {
                "name": name,
                "url": url,
                "lessons_groups": []
            }
            course_data["weeks"].append(week_data)
        
        print("Week links:")
        for week in course_data["weeks"]:
            print(week["url"])

        for i in range(len(course_data["weeks"])):
            week = course_data["weeks"][i]
            url = week["url"]
            week_data = self.get_week_data(url)
            week["name"] += f" {week_data['name']}"
            week["lessons_groups"] = week_data["lessons_groups"]
        
        return course_data

    def download_course(self, url, download_path):
        if not isinstance(type(download_path), pathlib.Path):
            download_path = pathlib.Path(download_path)

        course_data = self.get_course_data(url)
        file_name = _prepare_name(course_data["name"])
        with open(download_path / f"{file_name}.json", "w", encoding="utf-8") as file:
            json.dump(course_data, file, indent=2)

        self.download_by_course_data(course_data, download_path)
        
    def download_by_course_data(self, course_data, download_path):
        course_name = _prepare_dir_name(course_data["name"])
        for week_index, week_data in enumerate(course_data["weeks"]):
            week_name = _prepare_dir_name(week_data["name"])
            print(week_name)

            for group_index, lesson_group_data in enumerate(week_data["lessons_groups"]):
                lesson_group_name = f'{group_index+1} {_prepare_dir_name(lesson_group_data["name"])}'
                print(f"\t{lesson_group_name}")
                
                for lesson_index, lesson_data in enumerate(lesson_group_data["lessons"]):
                    lesson_name = f'{lesson_index+1} {_prepare_dir_name(lesson_data["name"])}'
                    lesson_type = lesson_data["type"]
                    lesson_url = lesson_data["url"]
                    video_download_path = download_path / course_name / week_name / lesson_group_name / lesson_name
                    print(f"\t\t{lesson_name}")

                    if not video_download_path.exists():
                        os.makedirs(video_download_path)
                    
                    if lesson_type.lower() == "video":
                        self.download_from_video_page(lesson_url, video_download_path)
        

            

def main(args_):
    command_parser = CommandParserBuilder.build()
    args = command_parser.parse_args(args_[1:])

    url = args.url
    download_path = pathlib.Path(args.download_path)

    # url = "https://www.coursera.org/learn/neural-networks-deep-learning/home/week/1"
    # url = "https://www.coursera.org/learn/deep-neural-network/home/week/1"
    # download_path = pathlib.Path("D:\\Coursera\DeepLearning.AI\\")

    coursera_parser = CourseraParser()
    coursera_parser.login(ROOT_DIR / "cookies" / "cookies_knu.pkl")

    if args.load_cookies:
        cookies_path = args.load_cookies
        coursera_parser.login(cookies_path)
    
    if args.get_course_data:
        course_data = coursera_parser.get_course_data(url)
        file_name = _prepare_name(course_data['name'])
        with open(download_path / f"{file_name}.json", "w", encoding="utf-8") as file:
            json.dump(course_data, file, indent=2)

    if args.download_course_by_data:
        course_data_path = pathlib.Path(args.download_course_by_data)
        
        course_data = None 
        with open(course_data_path, "r", encoding="utf-8") as file:
            course_data = json.load(file)

        assert course_data is not None, "Course data json is empty"

        coursera_parser.download_by_course_data(course_data, download_path=download_path)

    if args.user_control:
        coursera_parser.user_control()

    if args.save_cookies:
        cookies_path = pathlib.Path(args.save_cookies)
        coursera_parser.save_cookies(cookies_path)

if __name__ == "__main__":
    main(sys.argv)