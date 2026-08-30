"""Text cleaning and validation utilities."""

import re
from typing import Optional


def remove_code_tags(text: str) -> str:
    """Remove markdown code fences from text.
    
    Handles both fenced code blocks (```lang ... ```) and inline code (`...`).
    
    Args:
        text: Input text that may contain markdown code fences.
        
    Returns:
        Text with code fences removed, preserving the content inside.
    """
    # Remove fenced code blocks (```language\n...\n```)
    text = re.sub(r"```[a-zA-Z]*\n?(.*?)\n?```", r"\1", text, flags=re.DOTALL)
    return text


def remove_repeated_phrases(text: str) -> str:
    """Remove consecutive repeated phrases caused by model repetition glitches.

    A repeated 3-6 word phrase is collapsed as soon as it repeats once, since
    natural writing essentially never restates a whole phrase back to back —
    that pattern is a hallmark of an HTR/LLM repetition loop. A repeated
    1-2 word phrase is left alone until it repeats 3+ times in a row, since
    short doublings ("no no", "very very", "ha ha", a repeated place or day
    name) are common in ordinary writing and this is a historical-document
    transcription tool where preserving exactly what was written matters.

    Args:
        text: Input text that may contain repeated phrases.

    Returns:
        Text with runaway repeated phrases collapsed to a single occurrence.
    """
    long_phrase = r"(\b\w+(?: \w+){2,5}\b)( \1)+"
    text = re.sub(long_phrase, r"\1", text)

    short_phrase = r"(\b\w+(?: \w+)?\b)( \1){2,}"
    text = re.sub(short_phrase, r"\1", text)

    return text


def remove_repeated_lines(text: str) -> str:
    """Remove consecutive repeated lines.
    
    Args:
        text: Input text that may contain repeated lines.
        
    Returns:
        Text with consecutive identical lines collapsed.
    """
    lines = text.split('\n')
    result = []
    prev_line = None
    
    for line in lines:
        stripped = line.strip()
        if stripped != prev_line or stripped == '':
            result.append(line)
            prev_line = stripped
    
    return '\n'.join(result)


def normalize_whitespace(text: str) -> str:
    """Normalize excessive whitespace while preserving paragraph breaks.
    
    Args:
        text: Input text with potentially irregular whitespace.
        
    Returns:
        Text with normalized whitespace.
    """
    # Replace multiple spaces with single space
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Collapse more than 2 consecutive newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text


def clean_extracted_text(text: str) -> str:
    """Clean text extracted from HTR/OCR.
    
    Applies a series of cleaning operations:
    1. Remove markdown code fences
    2. Normalize whitespace
    3. Remove repeated phrases
    4. Remove repeated lines
    5. Strip leading/trailing whitespace
    
    Args:
        text: Raw extracted text.
        
    Returns:
        Cleaned text.
    """
    if not text:
        return ""
    
    text = remove_code_tags(text)
    text = normalize_whitespace(text)
    text = remove_repeated_phrases(text)
    text = remove_repeated_lines(text)
    
    return text.strip()


def extract_json_from_response(response: str) -> Optional[str]:
    """Extract JSON content from an LLM response.
    
    Handles common LLM response formats:
    - Raw JSON
    - JSON wrapped in markdown code fences (```json ... ```)
    - JSON with explanatory text before/after
    
    Args:
        response: LLM response text.
        
    Returns:
        Extracted JSON string, or None if no JSON found.
    """
    if not response:
        return None
    
    # First, try to extract from code fences
    code_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", response)
    if code_match:
        return code_match.group(1).strip()
    
    # Try to find a JSON array
    array_match = re.search(r"\[[\s\S]*\]", response)
    if array_match:
        return array_match.group()
    
    # Try to find a JSON object
    obj_match = re.search(r"\{[\s\S]*\}", response)
    if obj_match:
        return obj_match.group()
    
    return None


def validate_transcription(text: str, min_chars: int = 10) -> tuple[bool, str]:
    """Validate extracted transcription text.
    
    Args:
        text: Transcription text to validate.
        min_chars: Minimum character count for valid transcription.
        
    Returns:
        Tuple of (is_valid, message).
    """
    if not text:
        return False, "Empty transcription"
    
    cleaned = text.strip()
    
    if len(cleaned) < min_chars:
        return False, f"Transcription too short ({len(cleaned)} chars)"
    
    # Check if mostly illegible markers
    illegible_pattern = r'\[(?:illegible|unclear|\?)\]'
    illegible_matches = re.findall(illegible_pattern, cleaned, re.IGNORECASE)
    if len(illegible_matches) > len(cleaned) / 20:  # More than 5% illegible markers
        return False, f"High illegibility rate ({len(illegible_matches)} markers)"
    
    return True, "Valid"
