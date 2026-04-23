from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from src.config import Config

# Locators
EMAIL_INPUT = (By.NAME, "email")
PASSWORD_INPUT = (By.NAME, "current-password")
CONTINUE_BUTTON = (By.XPATH, "//div[text()='Continue']/ancestor::button")


def login(driver):
    """Perform an automated login on Patreon using the credentials specified in the `.env` file."""
    driver.get("https://www.patreon.com/login")

    # Enter email
    WebDriverWait(driver, 10).until(ec.presence_of_element_located(EMAIL_INPUT)).send_keys(Config.EMAIL)

    # Click continue button
    WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable(CONTINUE_BUTTON)
    ).click()

    # Enter password
    password_input = WebDriverWait(driver, 10).until(
        ec.presence_of_element_located((By.NAME, "current-password"))
    )
    WebDriverWait(driver, 10).until(ec.element_to_be_clickable(PASSWORD_INPUT))
    password_input.send_keys(Config.PASSWORD)

    # Click continue to login
    WebDriverWait(driver, 10).until(
        ec.element_to_be_clickable((By.XPATH, "//div[text()='Continue']/ancestor::button"))
    ).click()
