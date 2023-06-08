import os
import unittest
import shutil

from defines import ROOT_DIR
from defines import COOKIES_PATH
from defines import DEFAULT_SESSION_FNAME
from driver_builder import build_chrome_driver
from coursera_parser import CourseraParser


class TestCourseraParser(unittest.TestCase):
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


        driver = build_chrome_driver(
            headless=False, 
            no_logging=True, 
            detach=False, 
            download_path=storage_folder_path
        )
        coursera_parser = CourseraParser(driver)
        coursera_parser.login_by_cookies(COOKIES_PATH / DEFAULT_SESSION_FNAME)

        coursera_parser.download_from_video_page(url, storage_folder_path)

        downloaded_files = os.listdir(storage_folder_path)
        
        shutil.rmtree(storage_folder_path)
        
        print(f"Downloaded files:")
        print(downloaded_files)

        for file_name in file_names:
            self.assertTrue(file_name in downloaded_files)

if __name__ == "__main__":
    unittest.main()