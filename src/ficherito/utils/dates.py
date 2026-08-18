"""Date extraction and parsing utilities built on undate.

Dates are modeled with :class:`undate.Undate`, which represents partial and
uncertain dates (year-only, year-month, or full day precision). The helpers
here keep returning ISO strings / ``datetime`` so the rest of the codebase and
templates stay unchanged, while ``to_undate`` exposes the richer model.
"""

import re
from datetime import datetime
from typing import Optional

from undate import Undate

# Regex fragments used to locate date components inside a filename.
_FULL_DATE = re.compile(r"(?<!\d)(\d{4})[-_](\d{1,2})[-_](\d{1,2})(?!\d)")
_COMPACT_DATE = re.compile(r"(?<!\d)(\d{4})(\d{2})(\d{2})(?!\d)")
_YEAR_MONTH = re.compile(r"(?<!\d)(\d{4})[-_](\d{1,2})(?!\d)")
_YEAR_ONLY = re.compile(r"(?<!\d)(\d{4})(?!\d)")

# ISO / partial ISO string, e.g. 1892, 1892-03, 1892-03-15.
_ISO = re.compile(r"^\s*(\d{4})(?:-(\d{1,2}))?(?:-(\d{1,2}))?\s*$")


def _valid_year(year: int) -> bool:
    return 1000 <= year <= 2100


def _make_undate(year: int, month: Optional[int] = None, day: Optional[int] = None) -> Optional[Undate]:
    """Build an Undate, returning None if the components are out of range."""
    if not _valid_year(year):
        return None
    if month is not None and not 1 <= month <= 12:
        return None
    if day is not None and not 1 <= day <= 31:
        return None
    try:
        if day is not None:
            return Undate(year, month, day)
        if month is not None:
            return Undate(year, month)
        return Undate(year)
    except Exception:
        return None


def undate_from_filename(filename: str) -> Optional[Undate]:
    """Extract an :class:`undate.Undate` from a filename, or None if not found."""
    name = re.sub(r"\.[^.]+$", "", filename)

    match = _FULL_DATE.search(name) or _COMPACT_DATE.search(name)
    if match:
        undate = _make_undate(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        if undate is not None:
            return undate

    match = _YEAR_MONTH.search(name)
    if match:
        undate = _make_undate(int(match.group(1)), int(match.group(2)))
        if undate is not None:
            return undate

    match = _YEAR_ONLY.search(name)
    if match:
        undate = _make_undate(int(match.group(1)))
        if undate is not None:
            return undate

    return None


def to_undate(date_str: Optional[str]) -> Optional[Undate]:
    """Parse an ISO or partial-ISO date string into an :class:`undate.Undate`."""
    if not date_str:
        return None

    match = _ISO.match(date_str)
    if not match:
        return None

    year = int(match.group(1))
    month = int(match.group(2)) if match.group(2) else None
    day = int(match.group(3)) if match.group(3) else None
    return _make_undate(year, month, day)


def extract_date_from_filename(filename: str) -> Optional[str]:
    """Extract a date from a filename.

    Locates common date patterns and returns them as an ISO string
    (YYYY-MM-DD, YYYY-MM, or YYYY) via undate, or None if no date is found.

    Args:
        filename: Filename to extract date from.

    Returns:
        ISO date string, or None if no date found.
    """
    undate = undate_from_filename(filename)
    return str(undate) if undate is not None else None


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse a date string into a datetime object.

    Partial dates are resolved to their earliest possible day (e.g. "1892" ->
    1892-01-01) so they can be sorted and formatted. Falls back to a few common
    human-readable formats.

    Args:
        date_str: Date string to parse.

    Returns:
        datetime object, or None if parsing fails.
    """
    undate = to_undate(date_str)
    if undate is not None:
        earliest = undate.earliest
        return datetime(earliest.year, earliest.month, earliest.day)

    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
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
