import sys
import pathlib
import json

from command_parser import CommandParserBuilder
from driver_builder import build_chrome_driver
from defines import ROOT_DIR
from defines import COOKIES_PATH
from defines import WEBDRIVER_PATH
from defines import DOWNLOAD_PATH
from coursera_parser import CourseraParser
from utils import prepare_file_name
from utils import init 


def get_course_data(parser, url, download_path):
    course_data = parser.get_course_data(url)
    file_name = prepare_file_name(course_data["name"])
    prepared_file_name = prepare_file_name(file_name)

    with open(download_path / f"{prepared_file_name}.json", "w", encoding="utf-8") as file:
        json.dump(course_data, file, indent=2)


def download_course_by_data(parser, course_data_path, download_path):
    
    course_data = None 
    with open(course_data_path, "r", encoding="utf-8") as file:
        course_data = json.load(file)

    assert course_data is not None, "Course data json is empty"

    parser.download_by_course_data(course_data, download_path=download_path)


def main(args_):
    command_parser = CommandParserBuilder.build()
    parse_res = command_parser.parse_args(args_)
    
    init()

    driver = build_chrome_driver(
        headless=False, 
        tor=False, 
        no_logging=True,
        detach=False,
        download_path=DOWNLOAD_PATH
    )
    coursera_parser = CourseraParser(webdriver=driver)
    
    if parse_res.command == "get-course-data":
        url = parse_res.url
        cookies_path = COOKIES_PATH / parse_res.cookies

        coursera_parser.login_by_cookies(cookies_path)
        get_course_data(coursera_parser, url, DOWNLOAD_PATH)
    
    elif parse_res.command == "download-course":
        course_data_path = parse_res.path
        cookies_path = COOKIES_PATH / parse_res.cookies

        coursera_parser.login_by_cookies(cookies_path)
        download_course_by_data(coursera_parser, course_data_path, DOWNLOAD_PATH)
    
    elif parse_res.command == "login":
        email = parse_res.email
        password = parse_res.password
        file_name = parse_res.file_name

        coursera_parser.login_by_site(email, password)
        coursera_parser.save_cookies(COOKIES_PATH / file_name)

if __name__ == "__main__":
    main(sys.argv[1:])