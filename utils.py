import os
import time
import traceback
import random
import pathlib

from datetime import datetime
from PIL import Image
from bs4 import BeautifulSoup, NavigableString
from defines import WEBDRIVER_PATH
from defines import DOWNLOAD_PATH
from defines import COOKIES_PATH
from defines import TIMEOUT
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By


from pathlib import Path
from typing import Union
from typing import Callable
from typing import List


DEFAULT_REPEATER_ERRORS_TO_EXCEPT = (
    NoSuchElementException, 
    StaleElementReferenceException, 
    WebDriverException
)


def prepare_file_name(file_name:str) -> str:
    """
    Remove forbidden for file naming chars in windows
    
    Parameters
    ----------
    dir_name : str
        Input string

    Returns
    -------
    str 
        String without forbidden chars
    """
    
    to_replace = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\n", "\r"]
    for symbol in to_replace:
        file_name = file_name.replace(symbol, "")  
    
    return file_name


def prepare_dir_name(dir_name:str, max_name_len:int = 30) -> str:
    """
    Remove forbidden for dir naming chars in windows

    Parameters
    ----------
    dir_name : str
        Input string

    Returns
    -------
    str 
        String without forbidden chars
    """
    
    dir_name = prepare_file_name(dir_name)
    if len(dir_name) > max_name_len:
        dir_name = f"{dir_name[:max_name_len]}"

    to_replace = ["."]
    for symbol in to_replace:
        dir_name = dir_name.replace(symbol, "")  
    
    return dir_name.strip()


def get_inner_text(parent:BeautifulSoup) -> str:
    """
    Gets text only inner the block, without texts inside her childs 

    Parameters
    ----------
    parent : BeautifulSoup
        Input element

    Returns
    -------
    str
        Text inside element

    Examples
    --------
    html = \"\"\"
        <div>
            Some text inside block
            <span>Some text inside child span</span>
        </div>
    \"\"\"

    document = BeautifulSoup(html, "html.parser")
    print(get_inner_text(document)) # Prints: Some text inside block
    """
    
    return ''.join(parent.find_all(text=True, recursive=False)).strip()


# def get_inner_text(outer:BeautifulSoup):
#     inner_text = [element for element in outer if isinstance(element, NavigableString)]
#     return inner_text


def make_dirs_if_not_exists(path:Union[str, pathlib.Path]):
    """
    Make dirst if not exists

    Parameters
    ----------
    path : str | pathlib.Path
        Path (dirs)
    """

    if not os.path.isdir(path):
        os.makedirs(path)
        return True
    
    return False


def init():
    """
    Create required dirs, check dependecies
    """
    
    make_dirs_if_not_exists(DOWNLOAD_PATH)
    make_dirs_if_not_exists(COOKIES_PATH)


def repeater(timeout:float, 
             retry:int = 5, 
             random_timeout_function:Callable[[], float] = random.random, 
             errors = DEFAULT_REPEATER_ERRORS_TO_EXCEPT):
    """
    Repeat function 'retry' times

    Parameters
    ----------
    timeout : int | float
        Times between tries.
    
    retry : int
        Count of tries.

    random_timeout_function : Callable[[], float]
        Time noise added to waiting.

    errrors : Exception | Tuple[Exception]
        Single error or list/tuple of exceptions that must be excepted

    
    """    
    
    def inner(function):
        def wrapper(*args, **kwargs):
            iteration = 0
            
            ms_timeout = timeout / 1000
            ms_random_timeout_function = lambda: random_timeout_function() / 1000

            while ((retry is not None) and (iteration < retry)) or (retry is None):
                iteration += 1
                
                try:
                    return function(*args, **kwargs)
                except errors as e:
                    # traceback.print_exc()
                    print(traceback.format_exc())
                
                time.sleep(ms_timeout + ms_random_timeout_function())
            
            raise Exception(f"Repeater was tried about {retry} times without results")
        return wrapper
    return inner


def close_tabs(driver:RemoteWebDriver, save_tabs:List[int] = [0]):
        """ Close all tabs opened by extension """
        wait = WebDriverWait(driver, TIMEOUT)
        wait.until(
            lambda driver: len(driver.window_handles) > 1
        )
        
        tabs_mask = [False for _ in range(len(driver.window_handles))]
        for tab_index in save_tabs:
            tabs_mask[tab_index] = True
        
        pointer = 0
        while pointer < len(driver.window_handles):
            if tabs_mask[pointer]:
                 pointer += 1
                 continue
            
            driver.switch_to.window(driver.window_handles[pointer])
            driver.close()
            
            tabs_mask.pop(pointer)

        driver.switch_to.window(driver.window_handles[0])


def fullpage_screenshot(driver: RemoteWebDriver, 
                        scrolling_element: WebElement,
                        removing_elements: List[WebElement] = [], 
                        file: Union[str, Path] = DOWNLOAD_PATH / f"fullpage-screenshot_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png"):
    """
    Saves full page screenshot from selenium webdriver
    Originally modivicated from https://stackoverflow.com/questions/41721734/take-screenshot-of-full-page-with-selenium-python-with-chromedriver
    
    Slightly refactored by jekahamster
    :param driver: Selenium webdriber
    :param scrolling_element: WebElement that shoud be scrolled
    :param removing_elements: List of WebElements which should be deleted for image
    :param file: Filepath to save screenshot
    """

    for elem in removing_elements:        
        driver.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
        """, elem)

    total_width = int(scrolling_element.get_attribute("offsetWidth"))
    total_height = int(scrolling_element.get_attribute("scrollHeight"))
    viewport_width = int(scrolling_element.get_attribute("clientWidth"))
    viewport_height = int(scrolling_element.get_attribute("clientHeight"))
     
    rectangles = []
    i = 0
    while i < total_height:
        j = 0
        top_height = i + viewport_height
    
        if top_height > total_height:
            top_height = total_height
    
        while j < total_width:
            top_width = j + viewport_width
    
            if top_width > total_width:
                top_width = total_width
    
            rectangles.append((j, i, top_width,top_height))
    
            j += viewport_width
    
        i += viewport_height
    
    stitched_image = Image.new('RGB', (total_width, total_height))
    previous = None
    part = 0
    
    for rectangle in rectangles:
        if previous is not None:
            driver.execute_script("arguments[0].scrollTo({0}, {1})".format(rectangle[0], rectangle[1]), scrolling_element)
            time.sleep(0.2)
    
        file_name = "part_{0}.png".format(part)
    
        # driver.get_screenshot_as_file(file_name)
        scrolling_element.screenshot(file_name)
        screenshot = Image.open(file_name)
    
        if rectangle[1] + viewport_height > total_height:
            offset = (rectangle[0], total_height - viewport_height)
        else:
            offset = (rectangle[0], rectangle[1])
        stitched_image.paste(screenshot, offset)
        del screenshot
        os.remove(file_name)
        part += 1
        previous = rectangle
    
    stitched_image.save(file)