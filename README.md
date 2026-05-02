# PatreonScraper
A Selenium setup for scraping Patreon subscriptions

## Important Information

- This program requires a valid Patreon account with active subscriptions.
- No data nor credentials will be shared or exposed while using this application. Everything 
happens locally while a Selenium client scrapes the specified artists on Patreon.

### Data Structure

The output is a JSON file that has the following structure:
```json
[
  {
    "id": "<integer>",
    "title": "<string>",
    "date": "<YYYY-MM-DD>",
    "content": "<string>",
    "images": [
      "<string>",
      ...
    ],
    "attachments": [
      "<string>",
      ...
    ],
    "tags": [
      "<string>",
      ...
    ],
    "url": "<string>"
  }
]
```

| Field         | Type           | Description                                                                                                                          |
|---------------|----------------|--------------------------------------------------------------------------------------------------------------------------------------|
| `id`          | `<integer>`    | The Patreon id of this post. It's guaranteed unique.                                                                                 |
| `title`       | `<string>`     | The title of the post.                                                                                                               |
| `date`        | `<YYYY-MM-DD>` | The publish date of the post. The format is always `YYYY-MM-DD`.                                                                     |
| `content`     | `<string>`     | The body text of the post. Can be empty.                                                                                             |
| `images`      | `<string>`     | The images of the post. Relative path to the artist output folder. Between 0 and `N`.                                               |
| `attachments` | `<string>`     | The file attachments of the post (e.g. PDFs). Relative path to the artist output folder, stored alongside images. Between 0 and `N`. |
| `tags`        | `<string>`     | The tags of the post. Can be used to group or search posts. Between 0 and `M`.                                                       |
| `url`         | `<string>`     | The Patreon URL of the post.                                                                                                         |


## Setup

### Requirements

To run this project, you need to have
- Python (tested with 3.12)
- pip

installed on your machine.

### Installation

1. Clone this repository using:
```
git clone https://github.com/zaw4rud0/PatreonScraper.git
cd PatreonScraper
```
2. Install the required dependencies using:
```
pip install -r requirements.txt
```

### Configurations

#### Program Configuration

Make a copy of `.env.example` by running the following command:
```
cp .env.example .env
```
Replace the placeholder values in the `.env` file with the actual values.

#### Artists Configuration

Make a copy of `artists.example.json` by running the following command:
```
cp artists.example.json artists.json
```
In this file you can set the artists you want to scrape and define a tag mapping in case the artist has inconsistent tags on their posts.

### Running

1. Start the scraper:
```
python -m src.main
```
2. Run unit tests:
```
pytest
```

## Roadmap

- [x] Ability to scrape different artists in one run
- [x] Download images and attachments of scraped posts and place them in `/{OUTPUT_FOLDER}/{ARTIST}/images/{YEAR}/{MONTH}/`
- [ ] Ability to store scraped posts in a database out of the box
- [ ] More control over the scraping process, i.e. when the user wants to change the Patreon filters
- [ ] GUI window to show scraped posts, including their images. Use scraped tags to filter and search.
