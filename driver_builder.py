import os
import time
import pathlib

from defines import ROOT_DIR
from defines import EXTENSIONS_PATH
from utils import close_tabs
from selenium import webdriver
from selenium.webdriver import chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import firefox
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager 
from typing import Union


def _get_chrome_options(headless=True, tor=False, no_logging=False, detach=False, download_path="./downloads"):
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        if no_logging:
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        if detach:
            chrome_options.add_experimental_option("detach", True)
        
        if tor:
            chrome_options.add_argument("--proxy-server=socks5://127.0.0.1:9150")
        
        prefs = {
            "profile.default_content_setting_values.automatic_downloads": 1,
            "download.default_directory": str(download_path)   
        }

        # chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome Beta\\Application\\chrome.exe"
        chrome_options.add_experimental_option("prefs", prefs)

        return chrome_options


def add_extensions(options: Options, extensions_path:Union[str, pathlib.Path] = EXTENSIONS_PATH):
    if not isinstance(extensions_path, pathlib.Path):
        extensions_path = pathlib.Path(extensions_path)

    for path in extensions_path.glob("*.crx"):
        options.add_extension(path)


def build_chrome_driver(webdriver_path=None, headless=False, tor=False, no_logging=False, detach=False, download_path=None, extensions=False, fullscreen=False, window_size=(1920, 1080)):
    chrome_options = _get_chrome_options(headless=headless, tor=tor, no_logging=no_logging, detach=detach, download_path=download_path)
    executable_path = webdriver_path or ChromeDriverManager(path=str(ROOT_DIR)).install()
    service = chrome.service.Service(executable_path=str(executable_path))

    if extensions:
        add_extensions(chrome_options, EXTENSIONS_PATH)

    chrome_driver = webdriver.Chrome(service=service, options=chrome_options)

    if extensions:
        close_tabs(chrome_driver, save_tabs=[1])

    if fullscreen:
        chrome_driver.maximize_window()
    else:
        chrome_driver.set_window_size(window_size[0], window_size[1])

    return chrome_driver