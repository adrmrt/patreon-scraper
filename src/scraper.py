import asyncio
from selenium.common.exceptions import (
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    ElementClickInterceptedException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

from src.config import Config
from src.date_utils import parse_date
from src.logger import get_logger
from src.utils import download_post_attachments, download_post_images, save_posts_to_file

logger = get_logger(__name__)


def scrape_artist_posts(driver, artist, control=None):
    """
    Scrape posts from an artist's Patreon page, including loading more posts until the end.
    Handles consent modals or other obstructing elements.

    :param driver: Selenium WebDriver instance.
    :param artist: dict containing artist information with 'display_name' and 'url_name' keys.
    :param control: optional ScraperControl for pause/skip/quit support.
    :returns: A list of dictionaries, each representing a post's data.
    """
    url_name = artist["url_name"]

    artist_folder = Config.OUTPUT_FOLDER / url_name
    artist_folder.mkdir(parents=True, exist_ok=True)

    seen_post_ids = set()

    try:
        while True:
            new_posts = []

            # Wait for posts to load
            WebDriverWait(driver, 10).until(
                ec.presence_of_all_elements_located(
                    (By.XPATH, "//div[@data-tag='post-card']")
                )
            )

            # Extract all visible post elements
            post_elements = driver.find_elements(
                By.XPATH, "//div[@data-tag='post-card']"
            )

            # Filter out elements with IDs that have already been seen
            new_elements = [
                post
                for post in post_elements
                if extract_post_id(post) not in seen_post_ids
            ]

            # Process new elements
            for post in new_elements:
                post_data = extract_post_data(post, artist)
                if post_data and post_data["id"] not in seen_post_ids:
                    logger.info(
                        "Processed post %s - %s", post_data["id"], post_data["title"]
                    )
                    logger.debug("Found %d images.", len(post_data["images"]))

                    seen_post_ids.add(post_data["id"])
                    new_posts.append(post_data)

            session_cookies = {c["name"]: c["value"] for c in driver.get_cookies()}
            new_posts = asyncio.run(download_post_images(new_posts, artist_folder))
            new_posts = asyncio.run(download_post_attachments(new_posts, artist_folder, session_cookies))
            save_posts_to_file(new_posts, artist_folder)

            if control is not None:
                control.check_input()
                control.wait_if_paused()
                if control.quit or control.skip_artist:
                    break

            if not click_load_more(driver):
                break
    except TimeoutException:
        logger.warning("Timed out waiting for posts to load.")
    except Exception as e:
        logger.error("An error occurred: %s", e)


def click_load_more(driver):
    """
    Clicks the "Load more" button if it exists and is clickable.

    :param driver: Selenium WebDriver instance.
    :return: True if the button was clicked, False otherwise.
    """
    try:
        initial_post_count = len(
            driver.find_elements(By.XPATH, "//div[@data-tag='post-card']")
        )

        load_more_button = driver.find_element(
            By.XPATH,
            "//button[@type='button' and not(@aria-disabled='true') and .//div[text()='Load more']]",
        )
        if load_more_button.is_displayed():
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", load_more_button
            )
            load_more_button.click()

            # Wait for the number of posts to increase
            WebDriverWait(driver, 10).until(
                lambda d: (
                    len(d.find_elements(By.XPATH, "//div[@data-tag='post-card']"))
                    > initial_post_count
                )
            )
            return True
    except (NoSuchElementException, TimeoutException, ElementClickInterceptedException):
        pass
    return False


def extract_post_data(post_element, artist):
    """
    Extracts data from a single post element.

    :param post_element: WebElement representing a post.
    :param artist: The artist of the post.
    :returns: A dictionary containing the post's title, date, text, and tags, or None if extraction fails.
    """
    try:
        expand_post_content(post_element)

        title = get_element_text(post_element, ".//span[@data-tag='post-title']/a")
        date = extract_post_date(post_element)
        content = extract_post_text(post_element)
        tags = extract_post_tags(post_element, artist["tag_mapping"])

        images = extract_image_urls(post_element)
        attachments = extract_attachments(post_element)

        url = get_element_attribute(
            post_element, ".//span[@data-tag='post-title']/a", "href"
        )
        post_id = int(url.split("-")[-1])

        return {
            "id": post_id,
            "title": title,
            "date": date,
            "content": content,
            "images": images,
            "attachments": attachments,
            "tags": tags,
            "url": url,
        }

    except StaleElementReferenceException:
        pass
    except Exception:
        pass

    return None


def expand_post_content(post_element):
    """
    Expands the post content if a "Show more" button is present.

    :param post_element: WebElement representing a post.
    """
    try:
        show_more_button = post_element.find_element(
            By.XPATH, ".//button[contains(text(), 'Show more')]"
        )
        if show_more_button.is_displayed():
            for _ in range(2):
                try:
                    show_more_button.click()
                    WebDriverWait(post_element, 5).until(
                        ec.presence_of_all_elements_located(
                            (By.XPATH, ".//div[@class='sc-b20d4e5f-0 jOibYJ']/p")
                        )
                    )
                    return
                except TimeoutException:
                    continue
                except ElementClickInterceptedException:
                    continue
    except NoSuchElementException:
        pass


def get_element_text(parent, xpath):
    """
    Retrieves text content from a child element of the given parent.

    :param parent: Parent WebElement.
    :param xpath: str XPath to locate the child element.
    :returns: str Text content of the element or an empty string if not found.
    """
    try:
        element = parent.find_element(By.XPATH, xpath)
        return element.text.strip()
    except NoSuchElementException:
        return ""


def extract_post_date(post_element):
    """
    Extract the raw post date text from the post element.

    :param post_element: WebElement representing a post.
    :return: str The date or None if not found.
    """
    raw_date = get_element_text(
        post_element, ".//a[@data-tag='post-published-at']/span/span"
    ) or get_element_text(post_element, ".//a[@data-tag='post-published-at']/span")

    return parse_date(raw_date)


def get_element_attribute(parent, xpath, attribute):
    """
    Retrieves an attribute value from a child element of the given parent.

    :param parent: Parent WebElement.
    :param xpath: str XPath to locate the child element.
    :param attribute: str The attribute to retrieve (e.g., 'href').
    :returns: str Attribute value or an empty string if not found.
    """
    try:
        element = parent.find_element(By.XPATH, xpath)
        return element.get_attribute(attribute)
    except NoSuchElementException:
        return ""


def extract_post_text(post_element):
    """
    Extracts the text content from a post.

    :param post_element: WebElement representing a post.
    :returns: str Combined text content from all paragraphs.
    """
    paragraphs = post_element.find_elements(
        By.XPATH, ".//div[contains(@class, 'patreon-post-content')]//p"
    )
    logger.debug("extract_post_text: found %d paragraph(s).", len(paragraphs))

    texts = []
    for p in paragraphs:
        text = p.text.strip() or p.get_attribute("textContent").strip()
        if text:
            texts.append(text)

    return "\n".join(texts)


def extract_post_tags(post_element, tags_mapping):
    """
    Extracts tags from a post.

    :param post_element: WebElement representing a post.
    :param tags_mapping: The mapping of tags.
    :returns: list A list of tag strings.
    """
    raw_tags = post_element.find_elements(By.XPATH, ".//a[@data-tag='post-tag']")
    raw_tags_texts = [tag.text.strip().lower() for tag in raw_tags if tag.text.strip()]

    # Normalize tags based on the tag mapping
    effective_tags = []
    for raw_tag in raw_tags_texts:
        matched = False
        for mapping in tags_mapping:
            if raw_tag in mapping["alias"]:
                effective_tags.append(mapping["tag"])
                matched = True
                break

        if not matched:
            # If no mapping is found, keep the original tag
            effective_tags.append(raw_tag)

    return effective_tags


def extract_image_urls(post_element):
    """
    Extracts image URLs from a post.

    :param post_element: WebElement representing a post.
    :returns: list A list of image URLs or an empty list if none are found.
    """
    try:
        image_grid = post_element.find_elements(
            By.XPATH, ".//div[contains(@class, 'image-grid')]//img"
        )
        image_carousel = post_element.find_elements(
            By.XPATH, ".//div[contains(@class, 'image-carousel')]//img"
        )

        all_image_elements = image_grid + image_carousel

        # Extract the 'src' attribute of each image element
        image_urls = [img.get_attribute("src") for img in all_image_elements]
        return image_urls
    except NoSuchElementException:
        return []


def extract_attachments(post_element):
    """
    Extracts file attachments (e.g. PDFs) from a post.

    :param post_element: WebElement representing a post.
    :returns: list of dicts with 'url' and 'filename' keys.
    """
    try:
        links = post_element.find_elements(
            By.XPATH, ".//a[@data-tag='post-attachment-link']"
        )
        logger.debug("extract_attachments: found %d link(s).", len(links))
        attachments = []
        for link in links:
            url = link.get_attribute("href")  # Selenium resolves to absolute URL
            filename = link.text.strip()
            if not filename:
                # Fall back to the last path segment of the URL
                filename = url.split("/")[-1].split("?")[0] if url else ""
            if url and filename:
                attachments.append({"url": url, "filename": filename})
            elif url:
                logger.warning("Skipping attachment with no resolvable filename: %s", url)
        return attachments
    except NoSuchElementException:
        return []


def extract_post_id(post_element):
    """
    Extract the unique ID of a post from its element.

    :param post_element: WebElement representing a post.
    :returns: str The unique ID of the post or None if not found.
    """
    try:
        url = get_element_attribute(
            post_element, ".//span[@data-tag='post-title']/a", "href"
        )
        return int(url.split("-")[-1])
    except Exception:
        return None
