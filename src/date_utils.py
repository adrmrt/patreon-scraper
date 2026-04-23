from datetime import datetime, timedelta


def is_leap_year(year):
    """
    Checks if a given year is a leap year.
    :param year: The year to check.
    :return: True if the year is a leap year, False otherwise.
    """
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def parse_relative_date(raw_date, today):
    """
    Handles relative date parsing, e.g., "today", "yesterday", "5 days ago", etc.
    :param raw_date: str Raw relative date.
    :param today: datetime Current date.
    :return: str Parsed date in 'YYYY-MM-DD' format or None if not relative.
    """
    if raw_date == "today":
        return today.strftime("%Y-%m-%d")
    elif "minutes ago" in raw_date:
        try:
            minutes_ago = int(raw_date.split()[0])
            return (today - timedelta(minutes=minutes_ago)).strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid 'minutes ago' format: {raw_date}")
    elif raw_date == "yesterday":
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif "days ago" in raw_date:
        try:
            days_ago = int(raw_date.split()[0])
            return (today - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid 'days ago' format: {raw_date}")
    elif "an hour ago" in raw_date:
        return (today - timedelta(hours=1)).strftime("%Y-%m-%d")
    elif "hours ago" in raw_date:
        try:
            hours_ago = int(raw_date.split()[0])
            return (today - timedelta(hours=hours_ago)).strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid 'hours ago' format: {raw_date}")
    return None


def find_closest_february_29(today):
    """
    Finds the closest February 29th that is before or equal to the current date.
    :param today: datetime Current date.
    :return: str Date of the closest February 29th in 'YYYY-MM-DD' format.
    """
    year = today.year
    while True:
        if is_leap_year(year):
            try:
                leap_date = datetime(year, 2, 29)
                if leap_date <= today:
                    return leap_date.strftime("%Y-%m-%d")
            except ValueError:
                pass
        year -= 1


def parse_absolute_date(raw_date, today):
    """
    Handles absolute date parsing, e.g., "November 26", "Nov 26, 2020", etc.
    :param raw_date: str Raw absolute date.
    :param today: datetime Current date.
    :return: str Parsed date in 'YYYY-MM-DD' format.
    """
    try:
        # Case: "Nov 26, 2024"
        if "," in raw_date:
            return datetime.strptime(raw_date, "%b %d, %Y").strftime("%Y-%m-%d")
        # Case: "November 26"
        else:
            month_day = datetime.strptime(raw_date, "%B %d")
            year = today.year
            # Adjust year if the month/day hasn't occurred yet this year
            if month_day.month > today.month or (month_day.month == today.month and month_day.day > today.day):
                year -= 1
            return datetime(year, month_day.month, month_day.day).strftime("%Y-%m-%d")
    except ValueError as ve:
        raise ValueError(f"Invalid absolute date format: {raw_date} ({ve})")


def parse_date(raw_date):
    """
    Parses and normalizes a raw date string to the format 'YYYY-MM-DD'.
    Handles relative and absolute date formats.
    :param raw_date: str Raw date input.
    :return: str Parsed date in 'YYYY-MM-DD' format or None if parsing fails.
    """
    if not raw_date:
        return None  # Return None if input is empty or None

    raw_date = raw_date.strip().lower()  # Normalize input
    today = datetime.now()

    try:
        # Check for relative dates
        relative_date = parse_relative_date(raw_date, today)
        if relative_date:
            return relative_date

        # Handle special case: "February 29"
        if raw_date == "february 29":
            return find_closest_february_29(today)

        # Handle absolute dates
        return parse_absolute_date(raw_date, today)

    except ValueError as ve:
        print(f"ValueError parsing date '{raw_date}': {ve}")
    except Exception as e:
        print(f"Unexpected error parsing date '{raw_date}': {e}")

    return None
