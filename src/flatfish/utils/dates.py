"""Date extraction and parsing utilities."""

import re
from datetime import datetime
from typing import Optional


# Common date patterns in filenames
DATE_PATTERNS = [
    # ISO format: 2024-01-15, 2024_01_15
    (r"(\d{4})[-_](\d{2})[-_](\d{2})", "%Y-%m-%d"),
    # Compact: 20240115
    (r"(\d{4})(\d{2})(\d{2})", "%Y%m%d"),
    # US format: 01-15-2024, 01_15_2024
    (r"(\d{2})[-_](\d{2})[-_](\d{4})", "%m-%d-%Y"),
    # European format: 15-01-2024
    (r"(\d{2})[-_](\d{2})[-_](\d{4})", "%d-%m-%Y"),
    # Year-month: 2024-01, 2024_01
    (r"(\d{4})[-_](\d{2})(?!\d)", "%Y-%m"),
    # Historical formats: 1892-03-15
    (r"(\d{4})[-_](\d{1,2})[-_](\d{1,2})", "%Y-%m-%d"),
    # Just year: 1892
    (r"(?<!\d)(\d{4})(?!\d)", "%Y"),
]


def extract_date_from_filename(filename: str) -> Optional[str]:
    """Extract a date from a filename.

    Tries multiple common date patterns and returns the first match
    in ISO format (YYYY-MM-DD or YYYY-MM or YYYY).

    Args:
        filename: Filename to extract date from.

    Returns:
        Date string in ISO format, or None if no date found.
    """
    # Remove extension
    name = re.sub(r"\.[^.]+$", "", filename)

    for pattern, fmt in DATE_PATTERNS:
        match = re.search(pattern, name)
        if match:
            try:
                groups = match.groups()
                date_str = "-".join(groups)

                # Try to parse and validate
                if len(groups) == 3:
                    # Full date
                    year = int(groups[0]) if len(groups[0]) == 4 else int(groups[2])
                    month = int(groups[1]) if len(groups[0]) == 4 else int(groups[0])
                    day = int(groups[2]) if len(groups[0]) == 4 else int(groups[1])

                    # Validate ranges
                    if 1000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        return f"{year:04d}-{month:02d}-{day:02d}"

                elif len(groups) == 2:
                    # Year-month
                    year = int(groups[0])
                    month = int(groups[1])
                    if 1000 <= year <= 2100 and 1 <= month <= 12:
                        return f"{year:04d}-{month:02d}"

                elif len(groups) == 1:
                    # Just year
                    year = int(groups[0])
                    if 1000 <= year <= 2100:
                        return f"{year:04d}"

            except (ValueError, IndexError):
                continue

    return None


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string into a datetime object.

    Handles various formats including partial dates.

    Args:
        date_str: Date string to parse.

    Returns:
        datetime object, or None if parsing fails.
    """
    if not date_str:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%B %d, %Y",  # January 15, 2024
        "%b %d, %Y",  # Jan 15, 2024
        "%d %B %Y",   # 15 January 2024
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


def sort_by_date(items: list, date_key: str = "date", reverse: bool = False) -> list:
    """Sort a list of items by date.

    Items without dates are placed at the end.

    Args:
        items: List of dictionaries or objects with date attribute.
        date_key: Key or attribute name for the date.
        reverse: If True, sort in descending order.

    Returns:
        Sorted list.
    """
    def get_date(item):
        if isinstance(item, dict):
            date_str = item.get(date_key)
        else:
            date_str = getattr(item, date_key, None)

        if date_str:
            parsed = parse_date(date_str)
            if parsed:
                return (0, parsed)
        # Items without dates go to the end
        return (1, datetime.min)

    return sorted(items, key=get_date, reverse=reverse)


def format_date_display(date_str: Optional[str]) -> str:
    """Format a date string for display.

    Args:
        date_str: ISO date string (YYYY-MM-DD, YYYY-MM, or YYYY).

    Returns:
        Human-readable date string.
    """
    if not date_str:
        return "Unknown date"

    parsed = parse_date(date_str)
    if not parsed:
        return date_str

    # Format based on precision
    if len(date_str) == 4:  # Year only
        return date_str
    elif len(date_str) == 7:  # Year-month
        return parsed.strftime("%B %Y")
    else:  # Full date
        return parsed.strftime("%B %d, %Y")
