import os
import unittest
import shutil

from defines import ROOT_DIR
from defines import COOKIES_PATH
from defines import DEFAULT_SESSION_FNAME
from defines import WEBDRIVER_PATH
from driver_builder import build_chrome_driver
from coursera_parser import CourseraParser
from coursera_parser import week_page_items_paths


class TestCourseraParser(unittest.TestCase):
    def setUp(self):
        self.driver = build_chrome_driver(
            webdriver_path=WEBDRIVER_PATH,
            headless=False, 
            no_logging=True, 
            detach=False
        )


    def test_download_from_video_page(self):
        # TODO
        # Separate cookies for tests and cookies for exploitation

        # Depends from url
        # User specified
        url = "https://www.coursera.org/learn/machine-learning-probability-and-statistics/lecture/rJ080/course-introduction"
        file_names = [
            "Lecture Video (720p).mp4",
            "Lecture Video (240p).mp4",
            "Subtitles (English).vtt",
            "Transcript (English).txt"
        ]
        storage_folder_path = ROOT_DIR / ".tmp_tests"
        # --------------
        
        if storage_folder_path.exists():
            shutil.rmtree(storage_folder_path)

        os.makedirs(storage_folder_path)

        coursera_parser = CourseraParser(self.driver)
        coursera_parser.login_by_cookies(COOKIES_PATH / DEFAULT_SESSION_FNAME)

        coursera_parser.download_from_video_page(url, storage_folder_path)

        downloaded_files = os.listdir(storage_folder_path)
        
        shutil.rmtree(storage_folder_path)
        
        print(f"Downloaded files:")
        print(downloaded_files)

        for file_name in file_names:
            self.assertTrue(file_name in downloaded_files)

    def test_week_page(self):
        # User specified
        url = "https://www.coursera.org/learn/deep-neural-network/home/week/3"
        # --------------
        
        coursera_parser = CourseraParser(self.driver)
        week_data = coursera_parser.get_week_data(url)
        print(f"Week name: {week_data['name']}")
        for lessons_block in week_data:
            raise NotImplementedError


if __name__ == "__main__":
    unittest.main()