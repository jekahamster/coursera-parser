import sys 
import pickle
import json


def main(args):
    if len(args) < 1:
        raise ValueError(f"Args must contain pkl cookes file path as first parameter.")
    
    path = args[0]
    dict_data = None
    with open(path, "rb") as file:
        dict_data = pickle.load(file)

    list_data = []
    for dict_object in dict_data:
        list_object = list(dict_object.values())
        list_data.append(list_object)
    
    with open(f"{path}.txt", "w", encoding="UTF-8") as file:
        for list_object in list_data:
            file.write("\t".join(map(str, list_object)) + "\n")
    


if __name__ == "__main__":
    main(sys.argv[1:])