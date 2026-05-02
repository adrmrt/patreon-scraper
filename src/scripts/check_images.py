"""
Check that all image paths referenced in posts.json actually exist on disk.

Usage:
    python -m src.scripts.check_images
"""

import json

from src.config import Config
from src.logger import get_logger
from src.utils import load_artists

logger = get_logger(__name__)


def main():
    Config.validate()
    artists = load_artists(Config.ARTIST_FILE_PATH)

    total_missing = 0

    for artist in artists:
        url_name = artist["url_name"]
        artist_folder = Config.OUTPUT_FOLDER / url_name
        posts_file = artist_folder / "posts.json"

        if not posts_file.exists():
            logger.info("[%s] No posts.json, skipping.", url_name)
            continue

        with open(posts_file) as f:
            try:
                posts = json.load(f)
            except json.JSONDecodeError:
                logger.warning("[%s] Could not decode posts.json, skipping.", url_name)
                continue

        missing = []
        for post in posts:
            for rel_path in post["images"]:
                full_path = artist_folder / rel_path
                if not full_path.exists():
                    missing.append((post["id"], rel_path))

        if missing:
            logger.warning("[%s] %d missing image(s):", url_name, len(missing))
            for post_id, rel_path in missing:
                logger.warning("  post %s — %s", post_id, rel_path)
        else:
            logger.info("[%s] All images present.", url_name)

        total_missing += len(missing)

    if total_missing:
        logger.warning("Total missing: %d image(s).", total_missing)
    else:
        logger.info("All images accounted for.")


if __name__ == "__main__":
    main()
