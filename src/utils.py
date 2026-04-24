import json
import re
import aiohttp
import asyncio
from pathlib import Path
from datetime import datetime

from src.logger import get_logger

logger = get_logger(__name__)


def load_artists(file_path: Path) -> list[dict]:
    """
    Utility method to load artists from a JSON file.

    :param file_path: Path to the JSON file containing artist data.
    :return: List of artist dictionaries.
    """
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Artist file not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parsing JSON: {e}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename by removing or replacing invalid characters.
    """
    invalid_chars = r'<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


async def download_image(session, url: str, folder_path: Path) -> Path | None:
    """
    Downloads an image from a URL and saves it to a specified folder.

    :param session: An aiohttp ClientSession instance.
    :param url: The URL of the image to download.
    :param folder_path: The folder path where the image will be saved.
    :return: The absolute path to the downloaded image, or None on failure.
    """
    folder_path.mkdir(parents=True, exist_ok=True)

    try:
        async with session.get(url) as response:
            if response.status == 200:
                content_disposition = response.headers.get("Content-Disposition")
                if content_disposition:
                    match = re.search(r'filename="([^"]+)"', content_disposition)
                    file_name = match.group(1) if match else None
                else:
                    file_name = None

                # Fallback to using the basename of the URL
                if not file_name:
                    file_name = url.split("/")[-1]

                file_name = sanitize_filename(file_name)
                file_path = folder_path / file_name

                # Skip download if the file already exists
                if file_path.exists():
                    logger.debug("Skipping already downloaded file: %s", file_path)
                    return file_path

                with open(file_path, "wb") as f:
                    f.write(await response.read())

                logger.debug("Downloaded: %s -> %s", url, file_path)
                return file_path
            else:
                logger.warning("Failed to download %s: HTTP %s", url, response.status)
    except Exception as e:
        logger.error("Error downloading %s: %s", url, e)

    return None


async def download_post_images(posts: list[dict], output_folder: Path) -> list[dict]:
    """
    Download images for posts asynchronously and update their image attributes.

    :param posts: A list of post dictionaries with a 'date' and 'images' attribute.
    :param output_folder: Root output folder.
    :return: The list of posts with updated 'images' attributes.
    """
    async with aiohttp.ClientSession() as session:
        logger.debug("Output folder: %s", output_folder)

        tasks = []

        for post in posts:
            post_date = datetime.strptime(post["date"], "%Y-%m-%d")
            year = post_date.year
            month = f"{post_date.month:02d}"

            folder_path = output_folder / "images" / str(year) / str(month)
            for url in post["images"]:
                tasks.append(download_image(session, url, folder_path))

        downloaded_paths = await asyncio.gather(*tasks)

        index = 0
        for post in posts:
            updated_images = []
            for _ in post["images"]:
                path = downloaded_paths[index]
                if path is not None:
                    relative_path = Path(path).relative_to(output_folder)
                    logger.debug("Relative image path: %s", relative_path)
                    updated_images.append(str(relative_path))
                index += 1
            post["images"] = updated_images

    return posts


def save_posts_to_file(posts: list[dict], output_folder: Path) -> None:
    """
    Save posts to a JSON file, appending only new entries.

    :param posts: List of post dictionaries.
    :param output_folder: Path to the output folder of the specific artist.
    """
    posts_file = output_folder / "posts.json"
    existing_posts: list[dict] = []

    if posts_file.exists():
        with open(posts_file, "r") as file:
            try:
                existing_posts = json.load(file)
            except json.JSONDecodeError:
                logger.warning(
                    "Could not decode JSON from %s, starting fresh.", posts_file
                )

    existing_post_ids = {post["id"] for post in existing_posts}
    new_posts = [post for post in posts if post["id"] not in existing_post_ids]
    updated_posts = existing_posts + new_posts

    with open(posts_file, "w") as file:
        json.dump(updated_posts, file, indent=4)

    logger.info("Appended %d new posts to %s", len(new_posts), posts_file)
