import os 
import sys
import pathlib 
import argparse

from defines import ROOT_DIR


class StoreIfInputsAction(argparse.Action):
    def __init__(self, 
                option_strings, 
                dest, 
                nargs=None,
                const=None,
                default=None, 
                type=None,
                choices=None, 
                required=None,
                help=None,
                metavar=None):
        argparse.Action.__init__(
            self, 
            option_strings=option_strings, 
            dest=dest,
            nargs=nargs,
            const=const,
            default=default,
            type=type,
            choices=choices,
            required=required,
            help=help,
            metavar=metavar
        )

    def __call__(self, parser, namespace, values, option_string=None):
        print(values)
        print(option_string)



class CommandParserBuilder:
    def __init__(self):
        pass

    @staticmethod
    def build():
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-u", "--url",
            action="store",
            required=True,
            type=str,
        )
        parser.add_argument(
            "-g", "--get-course-data",
            action="store",
        )
        parser.add_argument(
            "-d", "--download-course-by-data",
            action="store"
        )
        parser.add_argument(
            "--save-cookies",
            action="store"
        )
        parser.add_argument(
            "--load-cookies",
            action="store"
        )
        parser.add_argument(
            "--user-control",
            action="store"
        )
        parser.add_argument(
            "--download-path",
            action="store",
            default="D:\Coursera\DeepLearning.AI"
        )

        return parser


def _main(args):
    parser = CommandParserBuilder.build()
    result = parser.parse_args(args)
    print(result)


if __name__ == "__main__":
    _main(sys.argv[1:])