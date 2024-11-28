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
    
    "lessons_groups": ".rc-LessonCollectionBody .rc-NamedItemListRefresh",
    "lessons_groups_names": ".cds-AccordionRoot-container .cds-AccordionRoot-container > h2 > button .cds-AccordionHeader-labelGroup span",
    "lessons_groups__lessons": "div[role='presentation']",
    "lessons_groups__lessons__link": "a",
    "lessons_groups__lessons__name": "p[data-test='rc-ItemName']",
    "lessons_groups__lessons__type": ".rc-WeekItemAnnotations > div:has(.rc-EffortText)",
    # "lessons_groups__lessons__type_class": "div",
    "lessons_groups__lessons__hidden_item": ".locked-tooltip" # TODO: No element found
   
}

lesson_type2action = {
    "": "screenshot",
    "video": "video",
    # "programming assignment": "code",
    "programming assignment": "screenshot",
    # "practice programming assignment": "code",
    "practice programming assignment": "screenshot",
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
    # "Lab": "code", 
    "Lab": "screenshot", 
    "Graded App Item": None,
    "Guided Project": None,
    # "Practice Assignment": "code",
    "Practice Assignment": "screenshot",
    "Graded Assignment": "quiz",
    "Peer-graded Assignment": "screenshot",
    "Graded App Item": "screenshot",
}

lesson_type_class2action = {
    "WeekSingleItemDisplay-lecture": "video",
    "WeekSingleItemDisplay-supplement": "screenshot",
    "WeekSingleItemDisplay-discussionPrompt": None,
    "WeekSingleItemDisplay-ungradedWidget": "screenshot", # Ungraded Plugin
    # "WeekSingleItemDisplay-exam": "quiz",
    "WeekSingleItemDisplay-exam": "screenshot",
    "WeekSingleItemDisplay-ungradedLti": "screenshot", # Ungraded App Item
    # "WeekSingleItemDisplay-ungradedLab": "code",
    "WeekSingleItemDisplay-ungradedLab": "screenshot",
    "WeekSingleItemDisplay-quiz": "quiz",
    # "WeekSingleItemDisplay-gradedProgramming": "code",
    "WeekSingleItemDisplay-gradedProgramming": "screenshot",
    "WeekSingleItemDisplay-ungradedProgramming": None,
    "WeekSingleItemDisplay-gradedLti": None,
    # "WeekSingleItemDisplay-ungradedAssignment": "code", # Practice Assignment 
    "WeekSingleItemDisplay-ungradedAssignment": "screenshot", # Practice Assignment 
    "WeekSingleItemDisplay-staffGraded": "quiz", # Graded Assignment
    "WeekSingleItemDisplay-phasedPeer": "screenshot",
    "WeekSingleItemDisplay-splitPeerReviewItem": "screenshot",
    "WeekSingleItemDisplay-gradedLti": "screenshot",
}

lesson_type2action = {k.lower() : v for k, v in lesson_type2action.items()}
lesson_type_class2action = {k.lower() : v for k, v in lesson_type_class2action.items()}


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


def _get_lesson_data(lesson_item:WebElement):
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
    # lesson_type_class = lesson_item_bs.select_one(week_page_items_paths["lessons_groups__lessons__type_class"])["data-test"]
    lesson_type_class = lesson_item.get_attribute("data-test")
    
    
    lesson_type_item = lesson_item_bs.select_one(week_page_items_paths["lessons_groups__lessons__type"])
    if not lesson_type_item:
        warnings.warn(f"Empty lesson_type at lesson '{lesson_name}'")

    lesson_type = get_inner_text(lesson_type_item) if lesson_type_item else ""
    lesson_type_descr = lesson_type_item.text if lesson_type_item else ""

    lesson_action = lesson_type2action[lesson_type.lower()]
    lesson_action_recheck = lesson_type_class2action[lesson_type_class.lower()]

    if lesson_url.startswith("/"):
        lesson_url = "https://www.coursera.org" + lesson_url

    assert lesson_action is not None, f"Lesson action for {lesson_type} is None.\n Specify what action should be done for this lesson type."
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


def _get_lessons_data(lessons_block:WebElement):
    time.sleep(2)

    lessons_items = WebDriverWait(lessons_block, TIMEOUT).until(
        lambda lessons_block: lessons_block.find_elements(By.CSS_SELECTOR, week_page_items_paths["lessons_groups__lessons"])
    )
    lessons_data = []

    for lesson_index, lesson_item in enumerate(lessons_items):
        print("Lesson index:", lesson_index)
        try:
            lesson_data = _get_lesson_data(lesson_item)
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


@repeater(TIMEOUT)
def get_week_data(driver: BaseWebDriver, url:str):
    print(f"Get week data")
    print(f"URL: {url}")
    print()

    driver.get(url)

    _wait_week_page_loading(driver=driver)

    week_name = driver.find_element(
        By.CSS_SELECTOR, 
        week_page_items_paths["week_name"]).text.strip()
    
    lessons_groups = driver.find_elements(
        By.CSS_SELECTOR, 
        week_page_items_paths["lessons_groups"])

    lossons_groups_names = driver.find_elements(
        By.CSS_SELECTOR, 
        week_page_items_paths["lessons_groups_names"])
    
    if len(lossons_groups_names) == 0 and len(lessons_groups) == 1:
        print("Single group week")
        lossons_groups_names = [week_name]
    else:
        assert len(lessons_groups) == len(lossons_groups_names), f"Lessons groups and lessons groups names are not match. Groups: {len(lessons_groups)}, Names: {len(lossons_groups_names)}"
        lossons_groups_names = [group_name.text.strip() for group_name in lossons_groups_names]
    
    week_data = {
        "name": week_name,
        "lessons_groups": []
    }

    for group_index, (lessons_group, lessons_groups__name)  in enumerate(zip(lessons_groups, lossons_groups_names)):
        print(lessons_groups__name)
        try:
            lessons_data = _get_lessons_data(lessons_group)
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


class WeekPageActions:
    @staticmethod
    def get_week_data(driver: BaseWebDriver, url:str):
        return get_week_data(driver, url)
    
    @staticmethod
    def wait_week_page_loading(driver:BaseWebDriver):
        return _wait_week_page_loading(driver)


def demo():
    from coursera_parser_legacy import CourseraParser
    from defines import DEFAULT_SESSION_FNAME
    from defines import COOKIES_PATH
    
    url = "https://www.coursera.org/learn/robotics-flight/home/module/1"
    # url = "https://www.coursera.org/learn/robotics-flight/home/module/4"

    driver = build_chrome_driver(webdriver_path=WEBDRIVER_PATH, headless=False, detach=True)
    coursera_parser = CourseraParser(driver)
    coursera_parser.login_by_cookies(COOKIES_PATH / DEFAULT_SESSION_FNAME)

    
    result = get_week_data(driver, url=url)
    json_str = json.dumps(result, indent=2)
    print(json_str)
    

if __name__ == "__main__":
    demo()