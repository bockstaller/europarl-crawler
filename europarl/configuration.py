import configparser


def read():
    """
    Reads configuration files from the local repository and ``/etc/europarl/settings.ini`` and returns a configparser object.

    Returns:
        configparser: configuration object created by merging both files
    """

    config = configparser.ConfigParser()

    file_locations = ["settings.ini", "/etc/europarl/settings.ini"]

    config.read(file_locations)
    return config
