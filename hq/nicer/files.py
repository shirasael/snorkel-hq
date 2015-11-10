__author__ = 'code-museum'

import os


def join_path(base_path, *continues):
    return os.path.join(base_path, *continues)


def check_path_existent(base_path, *continues):
    return os.path.exists(join_path(base_path, *continues))


def remove_file(base_path, *continues):
    return os.remove(join_path(base_path, *continues))


def create_folder(base_path, *continues):
    return os.mkdir(join_path(base_path, *continues))


def get_folder_items_names(base_path, *continues):
    return os.listdir(join_path(base_path, *continues))
