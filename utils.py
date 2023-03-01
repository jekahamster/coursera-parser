import os
import time
import traceback
import random

from bs4 import BeautifulSoup, NavigableString
from defines import WEBDRIVER_PATH
from defines import DOWNLOAD_PATH
from defines import COOKIES_PATH
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException


DEFAULT_REPEATER_ERRORS_TO_EXCEPT = (
    NoSuchElementException, 
    StaleElementReferenceException, 
    WebDriverException
)


def prepare_file_name(file_name):
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


def prepare_dir_name(dir_name, max_name_len=30):
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


def get_inner_text(parent:BeautifulSoup):
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


def make_dirs_if_not_exists(path):
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


def repeater(timeout, retry=5, random_timeout_function=random.random, errors=DEFAULT_REPEATER_ERRORS_TO_EXCEPT):
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
