import pytest
from app.core.url_extractor import extract_urls

def test_extract_simple_urls():
    """Test extraction of standard HTTP/HTTPS URLs."""
    text = "Check out https://google.com and http://example.org"
    urls = extract_urls(text)
    assert len(urls) == 2
    assert "https://google.com" in urls
    assert "http://example.org" in urls

def test_extract_urls_without_scheme():
    """Test that www.domain.com is converted to https://www.domain.com."""
    text = "Visit www.openai.com for info"
    urls = extract_urls(text)
    assert len(urls) == 1
    assert "https://www.openai.com" in urls

def test_extract_messy_input():
    """Test extraction from messy, real-world copy-paste text (brackets, commas)."""
    text = """
    Here is a list:
    1. https://site-a.com,
    2. (http://site-b.org)
    3. [www.site-c.net]
    """
    urls = extract_urls(text)
    assert len(urls) == 3
    assert "https://site-a.com" in urls
    assert "http://site-b.org" in urls
    assert "https://www.site-c.net" in urls

def test_deduplication():
    """Test that duplicate URLs are removed."""
    text = "https://duplicate.com and https://duplicate.com"
    urls = extract_urls(text)
    assert len(urls) == 1

def test_exclude_binary_files():
    """Ensure we don't extract links to binary files like PDFs or images."""
    text = "Read report at https://example.com/report.pdf or see https://example.com/image.png"
    urls = extract_urls(text)
    assert len(urls) == 0

def test_empty_input():
    """Test handling of empty or None input."""
    assert extract_urls("") == []
    assert extract_urls(None) == []