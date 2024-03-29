import os 
import sys
import pathlib 
import argparse
import dotenv

from defines import DOWNLOAD_PATH
from defines import DEFAULT_SESSION_FNAME

dotenv.load_dotenv()


def _setup_course_data_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "-u", "--url",
        action="store",
        required=True,
        type=str,
    )

    parser.add_argument(
        "--cookies",
        action="store",
        required=False,
        default=DEFAULT_SESSION_FNAME
    )

    return parser


def _setup_download_course_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "-p", "--path",
        action="store",
        required=True,
        type=str,
        help="Path to course data json"
    )

    parser.add_argument(
        "--cookies",
        action="store",
        required=False, 
        default=DEFAULT_SESSION_FNAME,
        help="Path to cookies"
    )

    return parser


def _setup_login_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--email",
        action="store",
        required=not os.environ.get("COURSERA_EMAIL"),
        default=os.environ.get("COURSERA_EMAIL")
    )

    parser.add_argument(
        "--password",
        action="store",
        required=not os.environ.get("COURSERA_PASSWORD"),
        default=os.environ.get("COURSERA_PASSWORD")
    )

    parser.add_argument(
        "--file-name",
        action="store",
        required=False,
        default=DEFAULT_SESSION_FNAME
    )

    return parser


def _setup_download_video_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "-u", "--url",
        action="store",
        required=True,
        type=str,
        help="Url to coursera video-lesson"
    )

    parser.add_argument(
        "-p", "--path",
        action="store",
        required=False,
        type=str,
        default=DOWNLOAD_PATH,
        help="Path to saving data"
    )

    parser.add_argument(
        "--cookies",
        action="store",
        required=False, 
        default=DEFAULT_SESSION_FNAME,
        help="Path to cookies"
    )

    return parser


class CommandParserBuilder:
    def __init__(self):
        pass
    
    @staticmethod
    def build():
        parser = argparse.ArgumentParser()

        subparsers = parser.add_subparsers(dest="command")

        course_data_parser = subparsers.add_parser("get-course-data", help="Get course data json from coursera")
        course_download_parser = subparsers.add_parser("download-course", help="Download course from coursera")
        login_parser = subparsers.add_parser("login", help="Login to coursera submodule. You also can create .env file like .env.example to set defatult params. After that you can use `login` command without --email and --password specfication")
        download_video_parser = subparsers.add_parser("download-video", help="Download single video from coursera")

        course_data_parser = _setup_course_data_parser(course_data_parser)
        course_download_parser = _setup_download_course_parser(course_download_parser)
        login_parser = _setup_login_parser(login_parser)
        download_video_parser = _setup_download_video_parser(download_video_parser)

        return parser


def _main(args):
    parser = CommandParserBuilder.build()
    result = parser.parse_args(args)
    print(result)


if __name__ == "__main__":
    _main(sys.argv[1:])