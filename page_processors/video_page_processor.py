import os
import time
import random
import requests
import threading
import colorama
import traceback

from pathlib import Path
from defines import ROOT_DIR
from defines import WEBDRIVER_PATH
from defines import TIMEOUT
from utils import prepare_file_name
from utils import repeater
from driver_builder import build_chrome_driver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.webdriver.remote.webelement import WebElement

from colorama import Fore
from typing import Union


colorama.init(autoreset=True)


video_page_items_paths = {
    "downloads_tab_button": "button[id$='DOWNLOADS']",
    "files_links": "a[download]",
    "video_name": "h1.video-name",
}


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


def _wait_video_downloads_tab_loading(driver: BaseWebDriver):
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


def _get_file_name_from_video_link_item(driver: BaseWebDriver, item: WebElement):
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



@repeater(TIMEOUT)
def download_from_video_page(driver: BaseWebDriver, url: str, download_path: Path):
    driver.get(url)
    
    downloads_tab_btn, video_name_item = _wait_video_page_loading(driver)

    if not download_path.exists():
        os.makedirs(download_path)

    downloads_tab_btn.click()
    time.sleep(1)
    
    files_links_items = _wait_video_downloads_tab_loading(driver)
    threads = []

    for item in files_links_items:
        time.sleep(random.random()*2)

        file_name = _get_file_name_from_video_link_item(driver, item)

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



class VideoPageActions:
    @staticmethod
    def download(driver: BaseWebDriver, url:str, download_path: Path):
        download_from_video_page(driver, url, download_path)
    
    @staticmethod
    def wait_loading(driver: BaseWebDriver):
        _wait_video_page_loading(driver)
        _wait_video_downloads_tab_loading(driver)


def demo():
    import shutil
    
    from datetime import datetime
    from coursera_parser_legacy import CourseraParser
    from defines import DEFAULT_SESSION_FNAME
    from defines import COOKIES_PATH
    
    # TODO
    # Separate cookies for tests and cookies for exploitation

    str_datetime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    url = "https://www.coursera.org/learn/robotics-flight/lecture/XguwZ/quadrotors"
    storage_folder_path = ROOT_DIR / "downloads" / f"test_{str_datetime}"
    
    if storage_folder_path.exists():
        shutil.rmtree(storage_folder_path)

    os.makedirs(storage_folder_path)

    driver = build_chrome_driver(webdriver_path=WEBDRIVER_PATH, headless=False, detach=True)

    coursera_parser = CourseraParser(driver)
    coursera_parser.login_by_cookies(COOKIES_PATH / DEFAULT_SESSION_FNAME)

    download_from_video_page(
        driver=driver, 
        url=url, 
        download_path=storage_folder_path)

    downloaded_files = os.listdir(storage_folder_path)
    
    shutil.rmtree(storage_folder_path)
    
    print(f"Downloaded files:")
    print("\n".join(downloaded_files))


        
if __name__ == "__main__":
    demo()