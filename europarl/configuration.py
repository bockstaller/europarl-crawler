import configparser


def read():
    config = configparser.ConfigParser()
    config.read("../settings.ini")
    return config
