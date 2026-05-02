"""
Merge posts from a second output folder into the current one.
Current posts take priority over imported posts on duplicate IDs.
Images referenced by newly added posts are copied from the source folder.

Usage:
    python -m src.scripts.import_posts <source_folder>
"""

import argparse
import json
import shutil
from pathlib import Path

from src.config import Config
from src.logger import get_logger
from src.utils import load_artists

logger = get_logger(__name__)


def _load_posts(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not decode %s, skipping.", path)
            return []


def _merge(current: list[dict], imported: list[dict]) -> tuple[list[dict], int]:
    """Return merged list and count of posts actually added."""
    current_ids = {post["id"] for post in current}  # set for O(1) lookup
    new_posts = [p for p in imported if p["id"] not in current_ids]
    return current + new_posts, len(
        new_posts
    )  # current first: preserves existing order


def _move_images(new_posts: list[dict], source_artist: Path, dest_artist: Path) -> int:
    """Move images for newly added posts. Returns count of files moved."""
    moved = 0
    for post in new_posts:
        for rel_path in post["images"]:
            src = source_artist / rel_path
            dst = dest_artist / rel_path
            if not src.exists():
                logger.warning("Source image not found, skipping: %s", src)
                continue
            if dst.exists():  # already present, don't overwrite
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(src, dst)
            moved += 1
    return moved


def main():
    parser = argparse.ArgumentParser(
        description="Merge posts from a source output folder into the current one."
    )
    parser.add_argument("source", type=Path, help="Path to the source output folder.")
    args = parser.parse_args()

    Config.validate()
    artists = load_artists(Config.ARTIST_FILE_PATH)

    for artist in artists:
        url_name = artist["url_name"]

        source_file = args.source / url_name / "posts.json"
        if not source_file.exists():
            logger.info("[%s] No posts.json in source, skipping.", url_name)
            continue

        current_file = Config.OUTPUT_FOLDER / url_name / "posts.json"
        current = _load_posts(current_file)
        imported = _load_posts(source_file)

        merged, added = _merge(current, imported)

        # Identify only the newly added posts to avoid copying images that already exist
        new_posts = merged[len(current) :]
        source_artist = args.source / url_name
        dest_artist = Config.OUTPUT_FOLDER / url_name

        moved = _move_images(new_posts, source_artist, dest_artist)

        dest_artist.mkdir(
            parents=True, exist_ok=True
        )  # artist folder may not exist yet
        with open(current_file, "w") as f:
            json.dump(merged, f, indent=4)

        skipped = len(imported) - added
        logger.info(
            "[%s] %d imported, %d added, %d skipped (duplicates). %d image(s) moved.",
            url_name,
            len(imported),
            added,
            skipped,
            moved,
        )


if __name__ == "__main__":
    main()
