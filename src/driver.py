from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from src.config import Config


def init_driver():
    """
    Initializes and returns a Selenium WebDriver instance for Firefox.

    This function configures the WebDriver using paths specified in the `Config` class.
    It sets the binary location for Firefox and the path to the GeckoDriver executable.
    The browser window is maximized upon initialization.

    :returns:
        selenium.webdriver.Firefox: An initialized WebDriver instance for automating Firefox.
    """
    options = Options()
    options.binary_location = str(Config.FIREFOX_PATH)
    service = Service(str(Config.GECKO_DRIVER_PATH))
    driver = webdriver.Firefox(service=service, options=options)
    driver.maximize_window()
    return driver
