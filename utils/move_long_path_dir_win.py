import shutil 
import argparse


def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--src', help='source file or directory')
    parser.add_argument('--dst', help='destination file or directory')
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    shutil.move(args.src, args.dst)


if __name__ == '__main__':
    main()