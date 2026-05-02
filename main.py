import time

from src.config import Config
from src.controls import ScraperControl, print_commands
from src.driver import init_driver
from src.logger import get_logger
from src.login import login
from src.scraper import scrape_artist_posts
from src.utils import load_artists

logger = get_logger(__name__)


def main():
    Config.validate()

    driver = init_driver()

    try:
        login(driver)

        # Wait for session to stabilize
        time.sleep(5)

        artists = load_artists(Config.ARTIST_FILE_PATH)
        control = ScraperControl()
        print_commands()

        for artist in artists:
            logger.info(
                "Scraping posts for artist: %s (%s)",
                artist["display_name"],
                artist["url_name"],
            )
            url = f"https://www.patreon.com/c/{artist['url_name']}/posts"
            driver.get(url)

            wait_for_user_to_dismiss_consent(control)

            while True:  # Rescrape loop: repeats this artist until the user skips
                scrape_artist_posts(driver, artist, control)

                if control.quit or control.skip_artist:
                    control.reset_artist()  # Clear flag before moving to next artist
                    break

                user_input = control.prompt(
                    "Press Enter to scrape this artist again. "
                    "To skip to the next artist, press any other key and then Enter: "
                )

                if user_input.strip():
                    break

            if control.quit:
                break
    finally:
        logger.info("Scraping complete.")
        # Always close the browser, even on error
        driver.close()


def wait_for_user_to_dismiss_consent(control):
    control.prompt(
        "Please dismiss the consent dialog (click the 'Reject non-essential' button) "
        "and press Enter to continue..."
    )
    logger.debug("User dismissed consent dialog, continuing.")


if __name__ == "__main__":
    main()
