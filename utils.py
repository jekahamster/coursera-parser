import os

from bs4 import BeautifulSoup, NavigableString
from defines import WEBDRIVER_PATH
from defines import DOWNLOAD_PATH
from defines import COOKIES_PATH


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
    
    to_replace = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
    for symbol in to_replace:
        file_name = file_name.replace(symbol, "")  
    
    return file_name


def prepare_dir_name(dir_name):
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
    if len(dir_name) > 30:
        dir_name = f"{dir_name[:30]}"

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




