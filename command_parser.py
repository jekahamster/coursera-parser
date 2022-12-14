import os 
import sys
import pathlib 
import argparse

from defines import DEFAULT_SESSION_FNAME


def _setup_course_data_parser(parser: argparse.ArgumentParser):
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


def _setup_download_course_parser(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-p", "--path",
        action="store",
        required=True,
        type=str
    )

    parser.add_argument(
        "--cookies",
        action="store",
        required=False, 
        default=DEFAULT_SESSION_FNAME
    )

    return parser


def _setup_login_parser(parser):
    parser.add_argument(
        "--email",
        action="store",
        required=True
    )

    parser.add_argument(
        "--password",
        action="store",
        required=True
    )

    parser.add_argument(
        "--file-name",
        action="store",
        required=False,
        default=DEFAULT_SESSION_FNAME
    )

    return parser



class CommandParserBuilder:
    def __init__(self):
        pass
    
    @staticmethod
    def build():
        parser = argparse.ArgumentParser()

        subparsers = parser.add_subparsers(dest="command")

        course_data_parser = subparsers.add_parser("get-course-data")
        course_download_parser = subparsers.add_parser("download-course")
        login_parser = subparsers.add_parser("login")

        course_data_parser = _setup_course_data_parser(course_data_parser)
        course_download_parser = _setup_download_course_parser(course_download_parser)
        login_parser = _setup_login_parser(login_parser)

        return parser


def _main(args):
    parser = CommandParserBuilder.build()
    result = parser.parse_args(args)
    print(result)


if __name__ == "__main__":
    _main(sys.argv[1:])