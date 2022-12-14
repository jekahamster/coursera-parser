import os 
import pathlib

from tabulate import tabulate


def _materials_count(path, counter, results, _paths=[]):
    files = os.listdir(path)
    for file in files:
        new_path = path / file

        if new_path.is_file() and path not in _paths:
            materials_cnt = len(os.listdir(path))
            _paths.append(path)
            main_files = 0
            for mat_file in os.listdir(path):
                if pathlib.Path(mat_file).suffix in (".mp4", ".vtt", ".txt", ".doc"):
                    main_files += 1

            results.append({"path": path, "count": materials_cnt, "has_main_files": main_files >= 6})

        elif new_path.is_dir():
            _materials_count(new_path, counter+1, results, _paths)


def materials_count(path):
    results = []
    _paths = []
    _materials_count(path, 0, results, _paths)
    return results


def check_materials_count(path):
    results = materials_count(path)
    results = filter(lambda item: item["count"] != 6, results)

    print(tabulate(results))

def main():
    path = pathlib.Path("D:\Coursera\DeepLearning.AI")
    check_materials_count(path)

if __name__ == "__main__":
    main()