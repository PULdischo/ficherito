"""Tests for text cleaning utilities."""

import pytest

from flatfish.utils.text import (
    remove_code_tags,
    remove_repeated_phrases,
    remove_repeated_lines,
    normalize_whitespace,
    clean_extracted_text,
    extract_json_from_response,
    validate_transcription,
)


class TestRemoveCodeTags:
    """Tests for remove_code_tags function."""

    def test_removes_fenced_code_block(self):
        text = "```json\n{\"key\": \"value\"}\n```"
        result = remove_code_tags(text)
        assert result == '{"key": "value"}'

    def test_removes_fenced_code_block_no_language(self):
        text = "```\nsome code\n```"
        result = remove_code_tags(text)
        assert result == "some code"

    def test_preserves_text_without_code_blocks(self):
        text = "Hello, world!"
        result = remove_code_tags(text)
        assert result == "Hello, world!"

    def test_handles_multiple_code_blocks(self):
        text = "Before ```python\ncode1\n``` middle ```js\ncode2\n``` after"
        result = remove_code_tags(text)
        assert result == "Before code1 middle code2 after"


class TestRemoveRepeatedPhrases:
    """Tests for remove_repeated_phrases function."""

    def test_removes_repeated_single_word(self):
        text = "the the quick fox"
        result = remove_repeated_phrases(text)
        assert result == "the quick fox"

    def test_removes_repeated_phrase(self):
        text = "I went to the store to the store yesterday"
        result = remove_repeated_phrases(text)
        assert result == "I went to the store yesterday"

    def test_preserves_non_repeated_text(self):
        text = "The quick brown fox jumps"
        result = remove_repeated_phrases(text)
        assert result == "The quick brown fox jumps"


class TestRemoveRepeatedLines:
    """Tests for remove_repeated_lines function."""

    def test_removes_consecutive_identical_lines(self):
        text = "Line 1\nLine 1\nLine 2"
        result = remove_repeated_lines(text)
        assert result == "Line 1\nLine 2"

    def test_preserves_blank_lines(self):
        text = "Line 1\n\n\nLine 2"
        result = remove_repeated_lines(text)
        assert result == "Line 1\n\n\nLine 2"

    def test_preserves_non_consecutive_identical_lines(self):
        text = "Line 1\nLine 2\nLine 1"
        result = remove_repeated_lines(text)
        assert result == "Line 1\nLine 2\nLine 1"


class TestNormalizeWhitespace:
    """Tests for normalize_whitespace function."""

    def test_collapses_multiple_spaces(self):
        text = "Hello    world"
        result = normalize_whitespace(text)
        assert result == "Hello world"

    def test_normalizes_tabs(self):
        text = "Hello\t\tworld"
        result = normalize_whitespace(text)
        assert result == "Hello world"

    def test_normalizes_line_endings(self):
        text = "Line 1\r\nLine 2\rLine 3"
        result = normalize_whitespace(text)
        assert result == "Line 1\nLine 2\nLine 3"

    def test_collapses_excessive_newlines(self):
        text = "Para 1\n\n\n\n\nPara 2"
        result = normalize_whitespace(text)
        assert result == "Para 1\n\nPara 2"


class TestCleanExtractedText:
    """Tests for clean_extracted_text function."""

    def test_applies_all_cleaning_steps(self):
        text = "```\nHello    world world\n```\n\n\n\nTest"
        result = clean_extracted_text(text)
        assert "```" not in result
        assert "    " not in result
        assert result.count("\n\n\n") == 0

    def test_strips_whitespace(self):
        text = "  \n  Hello  \n  "
        result = clean_extracted_text(text)
        assert result == "Hello"

    def test_handles_empty_string(self):
        result = clean_extracted_text("")
        assert result == ""


class TestExtractJsonFromResponse:
    """Tests for extract_json_from_response function."""

    def test_extracts_from_code_fence(self):
        response = "Here is the result:\n```json\n[{\"name\": \"John\"}]\n```"
        result = extract_json_from_response(response)
        assert result == '[{"name": "John"}]'

    def test_extracts_raw_array(self):
        response = '[{"name": "John"}]'
        result = extract_json_from_response(response)
        assert result == '[{"name": "John"}]'

    def test_extracts_raw_object(self):
        response = '{"name": "John"}'
        result = extract_json_from_response(response)
        assert result == '{"name": "John"}'

    def test_extracts_array_with_surrounding_text(self):
        response = 'Here are the entities: [{"name": "John"}] I hope this helps.'
        result = extract_json_from_response(response)
        assert result == '[{"name": "John"}]'

    def test_returns_none_for_no_json(self):
        response = "No JSON here, just plain text."
        result = extract_json_from_response(response)
        assert result is None

    def test_handles_empty_response(self):
        result = extract_json_from_response("")
        assert result is None


class TestValidateTranscription:
    """Tests for validate_transcription function."""

    def test_valid_transcription(self):
        text = "This is a valid transcription with enough content."
        is_valid, message = validate_transcription(text)
        assert is_valid
        assert message == "Valid"

    def test_empty_transcription(self):
        is_valid, message = validate_transcription("")
        assert not is_valid
        assert "Empty" in message

    def test_too_short_transcription(self):
        is_valid, message = validate_transcription("Hi", min_chars=10)
        assert not is_valid
        assert "too short" in message

    def test_high_illegibility(self):
        # Many illegible markers relative to text length
        text = "[illegible] a [?] b [unclear] c [illegible]"
        is_valid, message = validate_transcription(text)
        assert not is_valid
        assert "illegibility" in message
