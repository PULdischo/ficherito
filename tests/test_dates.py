"""Tests for date utilities."""

import pytest
from datetime import datetime

from ficherito.utils.dates import (
    extract_date_from_filename,
    parse_date,
    sort_by_date,
    format_date_display,
)


class TestExtractDateFromFilename:
    """Tests for extract_date_from_filename."""

    def test_iso_format(self):
        """Test ISO date format."""
        assert extract_date_from_filename("doc_2024-01-15.jpg") == "2024-01-15"
        assert extract_date_from_filename("2024_01_15_letter.png") == "2024-01-15"

    def test_compact_format(self):
        """Test compact date format."""
        assert extract_date_from_filename("doc20240115.jpg") == "2024-01-15"

    def test_historical_dates(self):
        """Test historical dates."""
        assert extract_date_from_filename("letter_1892-03-15.jpg") == "1892-03-15"
        assert extract_date_from_filename("1776_declaration.tiff") == "1776"

    def test_year_only(self):
        """Test year-only extraction."""
        assert extract_date_from_filename("document_1892.jpg") == "1892"

    def test_no_date(self):
        """Test files without dates."""
        assert extract_date_from_filename("letter_to_john.jpg") is None
        assert extract_date_from_filename("img001.png") is None


class TestParseDate:
    """Tests for parse_date."""

    def test_iso_date(self):
        """Test ISO format parsing."""
        result = parse_date("2024-01-15")
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_year_month(self):
        """Test year-month parsing."""
        result = parse_date("2024-01")
        assert result.year == 2024
        assert result.month == 1

    def test_year_only(self):
        """Test year-only parsing."""
        result = parse_date("1892")
        assert result.year == 1892

    def test_invalid_date(self):
        """Test invalid date returns None."""
        assert parse_date("not a date") is None
        assert parse_date("") is None


class TestSortByDate:
    """Tests for sort_by_date."""

    def test_sort_documents(self):
        """Test sorting documents by date."""
        docs = [
            {"id": "c", "date": "2024-03-01"},
            {"id": "a", "date": "2024-01-01"},
            {"id": "b", "date": "2024-02-01"},
        ]
        
        sorted_docs = sort_by_date(docs)
        
        assert [d["id"] for d in sorted_docs] == ["a", "b", "c"]

    def test_missing_dates_at_end(self):
        """Test that documents without dates go to end."""
        docs = [
            {"id": "a", "date": "2024-01-01"},
            {"id": "b", "date": None},
            {"id": "c", "date": "2024-02-01"},
        ]
        
        sorted_docs = sort_by_date(docs)
        
        assert sorted_docs[-1]["id"] == "b"


class TestFormatDateDisplay:
    """Tests for format_date_display."""

    def test_full_date(self):
        """Test full date formatting."""
        assert "January" in format_date_display("2024-01-15")
        assert "15" in format_date_display("2024-01-15")
        assert "2024" in format_date_display("2024-01-15")

    def test_year_month(self):
        """Test year-month formatting."""
        result = format_date_display("2024-01")
        assert "January" in result
        assert "2024" in result

    def test_year_only(self):
        """Test year-only formatting."""
        assert format_date_display("1892") == "1892"

    def test_unknown_date(self):
        """Test unknown date formatting."""
        assert format_date_display(None) == "Unknown date"
