import configparser


def read():
    config = configparser.ConfigParser()

    file_locations = ["settings.ini", "/etc/europarl/settings.ini"]

    config.read(file_locations)
    return config
