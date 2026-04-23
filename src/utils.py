import json
import re

import aiohttp
import asyncio
from pathlib import Path
from datetime import datetime

from src.config import Config


def load_artists(file_path="artists.json"):
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


async def download_image(session, url, folder_path: Path):
    """
    Downloads an image from a URL and saves it to a specified folder with the given file name.

    :param session: An aiohttp ClientSession instance.
    :param url: The URL of the image to download.
    :param folder_path: The folder path where the image will be saved.
    :return: The absolute path to the downloaded image.
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

                # Fallback to using the basename of URL
                if not file_name:
                    file_name = url.split("/")[-1]

                file_name = sanitize_filename(file_name)
                file_path = folder_path / file_name

                # Skip download if the file already exists
                if file_path.exists():
                    return file_path

                with open(file_path, "wb") as f:
                    f.write(await response.read())
                return file_path
            else:
                print(f"Failed to download {url}: {response.status}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None


async def download_post_images(posts, output_folder: Path):
    """
    Download images for posts asynchronously and updates their image attributes.

    :param posts: A list of post dictionaries with a 'date' and 'images' attribute.
    :param output_folder:
    :return: The list of posts with updated 'images' attributes.
    """
    async with aiohttp.ClientSession() as session:
        if Config.DEBUG:
            print(f"Output folder: {output_folder}")

        tasks = []

        for post in posts:
            post_date = datetime.strptime(post["date"], "%Y-%m-%d")
            year = post_date.year
            month = f"{post_date.month:02d}"

            folder_path = output_folder / "images" / str(year) / str(month)
            for url in post["images"]:
                tasks.append(download_image(session, url, folder_path))

        # Gather all results
        downloaded_paths = await asyncio.gather(*tasks)

        # Update post 'images' attributes
        index = 0
        for post in posts:
            updated_images = []
            for _ in post["images"]:
                relative_path = Path(downloaded_paths[index]).relative_to(output_folder)
                if Config.DEBUG:
                    print(relative_path)
                if relative_path:
                    updated_images.append(str(relative_path))
                index += 1
            post["images"] = updated_images

    return posts


def save_posts_to_file(posts, output_folder: Path):
    """
    Save posts to a JSON file for the given artist by appending new data to existing data.

    :param posts: List of post dictionaries.
    :param output_folder: Path to the output folder of the specific artist.
    """
    posts_file = output_folder / "posts.json"

    existing_posts = []

    # Load existing posts if the file exists
    if posts_file.exists():
        with open(posts_file, "r") as file:
            try:
                existing_posts = json.load(file)
            except json.JSONDecodeError:
                print(
                    f"Warning: Could not decode JSON from {posts_file}, starting fresh."
                )

    # Append only new posts (based on unique ID)
    existing_post_ids = {post["id"] for post in existing_posts}
    new_posts = [post for post in posts if post["id"] not in existing_post_ids]
    updated_posts = existing_posts + new_posts

    # Save the updated list of posts
    with open(posts_file, "w") as file:
        json.dump(updated_posts, file, indent=4)
    print(f"Appended {len(new_posts)} new posts to {posts_file}")
