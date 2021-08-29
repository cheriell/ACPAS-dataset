import sys


def format_path(path):
    # to linux path
    if sys.platform[:3] == 'win':
        path = path.replace('\\', '/')
    return path

def load_path(path):
    # to the system's path format
    if sys.platform[:3] == 'win':
        path = path.replace('/', '\\')
    return path
