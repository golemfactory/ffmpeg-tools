import os


def get_absolute_resource_path(filename):
    return os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'resources',
        filename
    )