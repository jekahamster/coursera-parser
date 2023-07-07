import sys 
import pickle
import json


def main(args):
    if len(args) < 1:
        raise ValueError(f"Args must contain pkl cookes file path as first parameter.")
    
    path = args[0]
    data = None
    with open(path, "rb") as file:
        data = pickle.load(file)
    
    with open(f"{path}.json", "w", encoding="UTF-8") as file:
        json.dump(data, file, indent=2)


if __name__ == "__main__":
    main(sys.argv[1:])