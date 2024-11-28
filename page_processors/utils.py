import time

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException



def resolve_honor_code(driver:BaseWebDriver, wait_sec:int = 10):
    honorcode_popup = "div[aria-describedby='Coursera Honor Code']"
    continue_button = "button[type='button'][data-testid='continue-button']"
    
    assert isinstance(driver, BaseWebDriver)
    
    try:
        wait = WebDriverWait(driver, wait_sec)
        window = wait.until(
            lambda driver: driver.find_element(
                By.CSS_SELECTOR,
                honorcode_popup
            ) 
        )
    except TimeoutException:
        window = None
        
    if window is not None:
        print("Honor code window found")
        honor_code_button = window.find_element(
            By.CSS_SELECTOR,
            continue_button
        )
        time.sleep(0.5)
        honor_code_button.click()
        print("Honor code accepted")
    else:
        print("Honor code window not found")

