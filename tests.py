import sys
import pathlib
import json
import base64

from command_parser import CommandParserBuilder
from defines import ROOT_DIR
from defines import WEBDRIVER_PATH
from coursera_parser import CourseraParser
from driver_builder import build_chrome_driver
from command_parser import CommandParserBuilder
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from utils import *
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.print_page_options import PrintOptions


def test_get_lesson_data(parser:CourseraParser):
    parser.login_by_cookies("./cookies/jekagolovkoknuua.pkl")
    parser.get_week_data("https://www.coursera.org/learn/deep-neural-network/home/week/1")


def test_argument_parser(args):
    parser = CommandParserBuilder.build()
    res = parser.parse_args(args)

    print(res)


def main():
    url = ""
    download_path = pathlib.Path("")
    driver = build_chrome_driver(
        webdriver_path=WEBDRIVER_PATH,
        headless=False,
        tor=False,
        no_logging=True,
        detach=False, 
        download_path=download_path
    )
    coursera_parser = CourseraParser(webdriver=driver)
    test_get_lesson_data(coursera_parser)


@repeater(timeout=300, errors=ValueError)
def some_function():
    print(1)
    raise ValueError
    print(2)


class A:
    @repeater(timeout=1, errors=ValueError)
    def some_function(self, param):
        print(param)
        print(1)
        raise ValueError
        print(2)


def repeater_test():
    some_function()


def test_bug():
    url = "https://www.coursera.org/learn/information-theory/lecture/nVbD7/assignment-5-video-preview"
    driver = build_chrome_driver(headless=False, no_logging=True, detach=True)
    cp = CourseraParser(driver)
    cp.login_by_cookies(pathlib.Path("./cookies/last-saved.pkl"))
    cp.download_from_video_page(url, pathlib.Path("./downloads"))


def test_repeater_class():
    a = A()
    a.some_function(12)



def test_week():
    driver = build_chrome_driver(no_logging=True, detach=False)
    url = "https://www.coursera.org/learn/intro-computer-vision/home/week/4"
    
    cp = CourseraParser(driver)
    cp.login_by_cookies("./cookies/last-saved.pkl")
    cp.get_week_data(url)
    print("Done")


def test_screenshot():
    from selenium.webdriver import Keys, ActionChains

    driver = build_chrome_driver(no_logging=True, detach=True, extensions=True)
    driver.get('https://selenium.dev/selenium/web/single_text_input.html')
    import time
    time.sleep(2)

    a = ActionChains(driver)
    a\
        .key_down(Keys.LEFT_SHIFT)\
        .key_down(Keys.LEFT_ALT)\
        .send_keys("p")\
        .perform()
    
    a\
        .key_up(Keys.LEFT_ALT)\
        .key_up(Keys.LEFT_SHIFT)\
        .perform()

    # assert driver.find_element(By.ID, "textInput").get_attribute('value') == "Ab"





import os
import time
from PIL import Image



# def fullpage_screenshot(driver:RemoteWebDriver, scrolling_element:WebElement, removing_elements, in_new_tab=False, file="./test.png"):
#     """
#     Saves full page screenshot from selenium webdriver
#     Originally copied from https://stackoverflow.com/questions/41721734/take-screenshot-of-full-page-with-selenium-python-with-chromedriver
#     (c) ihightower
#     Slightly refactored by pashawnn
#     :param driver: Selenium webdriber
#     :param file: Filename to save screenshot
#     """

#     for elem in removing_elements:        
#         driver.execute_script("""
#             var element = arguments[0];
#             element.parentNode.removeChild(element);
#         """, elem)

#     total_width = int(scrolling_element.get_attribute("offsetWidth"))
#     total_height = int(scrolling_element.get_attribute("scrollHeight"))
#     viewport_width = int(scrolling_element.get_attribute("clientWidth"))
#     viewport_height = int(scrolling_element.get_attribute("clientHeight"))
     
#     rectangles = []
#     i = 0
#     while i < total_height:
#         j = 0
#         top_height = i + viewport_height
    
#         if top_height > total_height:
#             top_height = total_height
    
#         while j < total_width:
#             top_width = j + viewport_width
    
#             if top_width > total_width:
#                 top_width = total_width
    
#             rectangles.append((j, i, top_width,top_height))
    
#             j += viewport_width
    
#         i += viewport_height
    
#     stitched_image = Image.new('RGB', (total_width, total_height))
#     previous = None
#     part = 0
    
#     for rectangle in rectangles:
#         if previous is not None:
#             driver.execute_script("arguments[0].scrollTo({0}, {1})".format(rectangle[0], rectangle[1]), scrolling_element)
#             time.sleep(0.2)
    
#         file_name = "part_{0}.png".format(part)
    
#         # driver.get_screenshot_as_file(file_name)
#         scrolling_element.screenshot(file_name)
#         screenshot = Image.open(file_name)
    
#         if rectangle[1] + viewport_height > total_height:
#             offset = (rectangle[0], total_height - viewport_height)
#         else:
#             offset = (rectangle[0], rectangle[1])
#         stitched_image.paste(screenshot, offset)
#         del screenshot
#         os.remove(file_name)
#         part += 1
#         previous = rectangle
    
#     stitched_image.save(file)


def test_page_screenshot():
    # url = "https://www.coursera.org/learn/machine-learning-probability-and-statistics/supplement/5mYZm/interactive-tool-relationship-between-pmf-pdf-and-cdf-of-some-distributions"
    url = "https://www.coursera.org"
    
    driver = build_chrome_driver(
        headless=False,
        no_logging=True,
        detach=False
    )
    cp = CourseraParser(driver)
    # cp.login_by_cookies("./cookies/last-saved.pkl")
    driver.get(url)
    time.sleep(3)
    # elem = driver.find_element(By.CSS_SELECTOR, ".ItemPageLayout_content_body")
    header = driver.find_element(By.TAG_NAME, "header")
    
    removing_elements = [
        header
    ]

    elem = driver.find_element(By.TAG_NAME, "html")
    fullpage_screenshot(driver, elem, removing_elements)


def test_page_screenshot2():
    # url = "https://www.coursera.org/learn/machine-learning-probability-and-statistics/supplement/5mYZm/interactive-tool-relationship-between-pmf-pdf-and-cdf-of-some-distributions"
    url = "https://www.coursera.org"
    
    driver = build_chrome_driver(
        headless=False,
        no_logging=True,
        detach=False
    )
    cp = CourseraParser(driver)
    # cp.login_by_cookies("./cookies/last-saved.pkl")
    driver.get(url)
    time.sleep(1)



def test_tabs():
    driver = build_chrome_driver(
        headless=False,
        no_logging=True,
        detach=False
    )

    driver.get("https://www.coursera.org")
    original_window = driver.current_window_handle
    assert len(driver.window_handles) == 1, "Other windows must be closed"

    driver.switch_to.new_window('tab') # 'tab' or 'window'

    WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))

    driver.get("https://stackoverflow.com/")
    
    text1 = driver.find_element(By.CSS_SELECTOR, ".-img._glyph").text
    print(text1)

    driver.close()
    driver.switch_to.window(original_window)

    time.sleep(1)
    text2 = driver.find_element(By.CSS_SELECTOR, "h2").text

    print(text1)
    print(text2)


def test_coursera_parser_screenshot():
    # url = "https://www.coursera.org/learn/machine-learning-probability-and-statistics/supplement/UEgpf/check-your-knowledge"
    url = "https://www.coursera.org/learn/machine-learning-probability-and-statistics/supplement/5mYZm/interactive-tool-relationship-between-pmf-pdf-and-cdf-of-some-distributions"
    driver = build_chrome_driver(
        webdriver_path=WEBDRIVER_PATH,
        headless=False,
        no_logging=True,
        detach=False
    )

    cp = CourseraParser(driver)
    cp.login_by_cookies("./cookies/last-saved.pkl")

    cp.download_from_reading_page(url=url, download_path=DOWNLOAD_PATH)



def test_quiz_downloading():
    from page_processors.quiz_page_processor import QuizPageActions
    # url = "https://www.coursera.org/learn/deep-neural-network/exam/1mKhR/hyperparameter-tuning-batch-normalization-programming-frameworks"
    url = "https://www.coursera.org/learn/robotics-flight/assignment-submission/A9BlE/3"
    # url = "https://www.coursera.org/learn/robotics-flight/assignment-submission/X27Te/1-2"
    
    driver = build_chrome_driver(
        headless=False,
        no_logging=True,
        detach=True
    )

    cp = CourseraParser(driver)
    cp.login_by_cookies("./cookies/last-saved.pkl")

    QuizPageActions.download(driver=driver, url=url, download_path=DOWNLOAD_PATH)



def test_week_data():
    url = "https://www.coursera.org/learn/machine-learning-probability-and-statistics/home/week/1"
    driver = build_chrome_driver(
        headless=False,
        no_logging=True,
        detach=True
    )

    cp = CourseraParser(driver)
    cp.login_by_cookies("./cookies/last-saved.pkl")

    res = cp.get_week_data(url)
    print(json.dumps(res, indent=2))


def test_downloading_programming_assignment():
    # url = "https://www.coursera.org/learn/chatgpt/ungradedLab/nXLwa/building-your-own-n-gram-language-model"
    # url = "https://www.coursera.org/learn/classification-vector-spaces-in-nlp/programming/P4CTb/logistic-regression"
    # url = "https://www.coursera.org/learn/classification-vector-spaces-in-nlp/ungradedLab/n1iZS/another-explanation-about-pca"
    url = "https://www.coursera.org/learn/classification-vector-spaces-in-nlp/ungradedLab/oq8uf/manipulating-word-embeddings"
    driver = build_chrome_driver(
        webdriver_path=WEBDRIVER_PATH,
        headless=False,
        no_logging=True,
        detach=True
    )

    cp = CourseraParser(driver)
    cp.login_by_cookies("./cookies/last-saved.pkl")

    cp.download_from_programming_assignment_page(url, DOWNLOAD_PATH)


def test_dynamic_downloading_path():
    url2 = "https://www.coursera.org/learn/convolutional-neural-networks/programming/OgKZl/face-recognition"
    url1 = "https://www.coursera.org/learn/convolutional-neural-networks/programming/4AZ8P/art-generation-with-neural-style-transfer"
    driver = build_chrome_driver(
        webdriver_path=WEBDRIVER_PATH,
        headless=False,
        no_logging=True,
        detach=False
    )

    cp = CourseraParser(driver)
    cp.login_by_cookies("./cookies/last-saved.pkl")

    path1 = DOWNLOAD_PATH / "_test_path1_1"
    path2 = DOWNLOAD_PATH / "_test_path2_1"
    path1.mkdir(exist_ok=True)
    path2.mkdir(exist_ok=True)

    cp.change_download_path(path1)
    cp.download_from_programming_assignment_page(url1, path1)
    time.sleep(3)
    cp.change_download_path(path2)
    cp.download_from_programming_assignment_page(url2, path2)


def test_download_from_video_page():
    from page_processors.video_page_processor import VideoPageActions
    url = "https://www.coursera.org/learn/robotics-capstone/lecture/fWzEv/introduction-to-the-mobile-inverted-pendulum-mip-track"
    
    driver = build_chrome_driver(headless=False, detach=True)
    parser = CourseraParser(driver)
    parser.login_by_cookies(COOKIES_PATH / "last-saved.pkl")
    
    VideoPageActions.download(driver=parser.driver, url=url, download_path=DOWNLOAD_PATH)
    

def test_download_from_reading_page():
    from page_processors.reading_page_processor import ReadingPageActions
    url = "https://www.coursera.org/learn/robotics-capstone/programming/Sluzx/b1-3-dijkstras-algorithm-in-python"
    
    driver = build_chrome_driver(headless=False, detach=True)
    parser = CourseraParser(driver)
    parser.login_by_cookies(COOKIES_PATH / "last-saved.pkl")
    
    ReadingPageActions.download(driver=parser.driver, url=url, download_path=DOWNLOAD_PATH)


if __name__ == "__main__":
    # main()
    # test_argument_parser(sys.argv[1:])
    # python coursera_parser.py get-course-data -p <path>
    # python coursera_parser.py download-by-course-data -p <path>
    # repeater_test()
    # test_bug()
    # test_repeater_class()
    # test_week()
    # test_page_screenshot()
    # test_page_screenshot2()
    # test_tabs()
    # test_quiz_downloading()
    # test_week_data()
    # test_downloading_programming_assignment()
    # test_dynamic_downloading_path()
    # test_coursera_parser_screenshot()
    # test_download_from_video_page()
    # test_download_from_reading_page()
    test_quiz_downloading()