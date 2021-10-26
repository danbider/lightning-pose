from operator import sub
import os
import pickle
from typeguard import typechecked
from typing import Any


@typechecked
def set_or_open_folder(folder_path: str) -> str:
    if not os.path.isdir(folder_path):
        os.makedirs(folder_path, exist_ok=True)
        print("Opened a new folder at: {}".format(folder_path))
    else:
        print("The folder already exists at: {}".format(folder_path))
    return folder_path


# pickle utils
@typechecked
def save_object(obj: Any, filename: str) -> None:
    with open(filename, "wb") as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


@typechecked
def load_object(filename: str) -> Any:
    with open(filename, "rb") as input:  # note rb and not wb
        return pickle.load(input)


@typechecked
def get_latest_version(lightning_logs_path: str) -> str:
    # TODO: add what's needed to pull out ckpts
    subfolders = os.listdir(lightning_logs_path)
    if ".DS_Store" in subfolders:
        subfolders.remove(".DS_Store")
    # ints = []
    # for l in subfolders:
    #     print(l)
    #     if l != '.DS_Store':
    #         ints.append(int(l.split('_')[-1]))
    #     else:
    #         subfolders.remove(l)
    ints = [int(l.split("_")[-1]) for l in subfolders]
    latest_version = subfolders[ints.index(max(ints))]
    print("version used: %s" % latest_version)
    return latest_version