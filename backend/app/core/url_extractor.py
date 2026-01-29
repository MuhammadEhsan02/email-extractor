"""
URL Extractor Module

Extracts and cleans URLs from raw input text.
Capable of handling raw text, CSV-like lists, and messy copy-pastes.

Author: Email Extraction System
"""

import re
import logging
from typing import List, Set
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Regex pattern to identify URLs starting with http:// or https://
# Handles common characters found in URLs while avoiding trailing punctuation
URL_PATTERN = re.compile(
    r'(https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
    r'https?://(?:[a-zA-Z0-9]+\.)+[a-zA-Z]{2,})'
)

def extract_urls(text: str) -> List[str]:
    """
    Parses raw input text and returns a list of unique, valid URLs.

    Args:
        text: Raw string input (e.g., pasted from Google Search, CSV, or text file).

    Returns:
        List[str]: A list of unique, validated absolute URLs.
    """
    if not text:
        logger.warning("Empty text provided to url_extractor.")
        return []

    # 1. Find all regex matches
    # We join lines to handle cases where input might be line-separated
    raw_matches = URL_PATTERN.findall(text)
    
    unique_urls: Set[str] = set()
    
    for match in raw_matches:
        clean_url = _clean_url(match)
        if clean_url:
            unique_urls.add(clean_url)

    # 2. Convert to list and sort for consistent processing order
    sorted_urls = sorted(list(unique_urls))
    
    logger.info(f"Extracted {len(sorted_urls)} unique URLs from input.")
    return sorted_urls

def _clean_url(raw_url: str) -> str:
    """
    Cleans and normalizes a single URL string.
    
    - Strips surrounding whitespace/punctuation.
    - Adds 'https://' if missing (e.g. if starts with 'www').
    - Validates structure via urllib.
    """
    # Remove common trailing punctuation that regex might catch (e.g., "example.com.")
    url = raw_url.strip(".,;:\"'()[]{}<>")
    
    # Ensure scheme exists
    if url.startswith("www."):
        url = "https://" + url
    elif not url.startswith(("http://", "https://")):
        # If no scheme and no www, it might be invalid, but we'll try adding https
        return None

    try:
        parsed = urlparse(url)
        # minimal validation: must have a domain (netloc)
        if not parsed.netloc:
            return None
            
        # Optional: Exclude common non-html extensions to save scraper resources
        path_lower = parsed.path.lower()
        if path_lower.endswith(('.pdf', '.jpg', '.png', '.gif', '.zip', '.exe', '.css', '.js')):
            return None

        return url
    except Exception:
        return None
    