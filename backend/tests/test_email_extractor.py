import pytest
from app.core.email_extractor import EmailExtractor

@pytest.fixture
def extractor():
    return EmailExtractor()

def test_extract_valid_emails(extractor):
    """Test extraction of standard valid emails."""
    text = "Contact us at support@example.com or sales@example.co.uk"
    emails = extractor.extract(text)
    
    assert len(emails) == 2
    assert emails[0].email == "support@example.com"
    assert emails[1].email == "sales@example.co.uk"

def test_filter_junk(extractor):
    """Test that invalid patterns looking like emails are rejected."""
    text = "Not emails: user@localhost, 12345@domain, @missinguser.com, user@.com"
    emails = extractor.extract(text)
    assert len(emails) == 0

def test_confidence_scoring(extractor):
    """Test that business emails get higher scores than free providers."""
    text = "business@corp.com vs personal@gmail.com"
    emails = extractor.extract(text)
    
    business = next(e for e in emails if e.email == "business@corp.com")
    personal = next(e for e in emails if e.email == "personal@gmail.com")
    
    assert business.confidence_score > personal.confidence_score

def test_deduplication_option():
    """Test removal of duplicates when configured."""
    extractor_nodup = EmailExtractor(remove_duplicates=True)
    text = "test@test.com test@test.com"
    results = extractor_nodup.extract(text)
    assert len(results) == 1

def test_context_capture(extractor):
    """Test that surrounding text is captured for context."""
    text = "Please reach out to help@desk.com for immediate assistance."
    results = extractor.extract(text)
    assert "immediate assistance" in results[0].source_context