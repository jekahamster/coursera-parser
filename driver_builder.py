import os
import time

from defines import ROOT_DIR
from selenium import webdriver
from selenium.webdriver import chrome
from selenium.webdriver import firefox
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager 


def _get_chrome_options(headless=True, tor=False, no_logging=False, detach=False, download_path="./downloads"):
        chrome_options = chrome.options.Options()
        
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


def build_chrome_driver(webdriver_path=None, headless=False, tor=False, no_logging=False, detach=False, download_path=None):
    chrome_options = _get_chrome_options(headless=headless, tor=tor, no_logging=no_logging, detach=detach, download_path=download_path)
    executable_path = webdriver_path or ChromeDriverManager(path=str(ROOT_DIR)).install()
    service = chrome.service.Service(executable_path=str(executable_path))

    chrome_driver = webdriver.Chrome(service=service, options=chrome_options)
    return chrome_driver