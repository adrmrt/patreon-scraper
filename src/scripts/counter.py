import json
from collections import defaultdict
from datetime import datetime

from src.config import Config
from src.utils import load_artists


def count_posts_per_year(artist):
    file_path = Config.OUTPUT_FOLDER / artist["url_name"] / "posts.json"

    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    try:
        # Read JSON file
        with open(file_path, "r", encoding="utf-8") as f:
            posts = json.load(f)

        year_count = defaultdict(int)

        for post in posts:
            date_str = post.get("date")
            if date_str:
                try:
                    post_date = datetime.strptime(date_str, "%Y-%m-%d")
                    year_count[post_date.year] += 1
                except ValueError:
                    print(f"Invalid date format for post: {date_str}")

        print(f"Artist: {artist['display_name']} ({artist['url_name']})")
        for year, count in sorted(year_count.items()):
            print(f"   {year}: {count} posts")

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")


artists = load_artists(Config.ARTIST_FILE_PATH)
for a in artists:
    count_posts_per_year(a)
