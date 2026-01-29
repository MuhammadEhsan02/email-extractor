import pytest
import aiohttp
from unittest.mock import AsyncMock, patch
from app.core.scraper import WebScraper

@pytest.mark.asyncio
async def test_scraper_success():
    """Test successful HTML retrieval with 200 OK status."""
    mock_html = "<html><body><h1>Test</h1></body></html>"
    
    # Mock the aiohttp ClientSession
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Configure mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {'Content-Length': '100'}
        # Mock async iterator for content
        mock_response.content.iter_chunked.return_value = [mock_html.encode('utf-8')]
        
        # Setup context manager return
        mock_get.return_value.__aenter__.return_value = mock_response
        
        scraper = WebScraper(respect_robots=False)
        result = await scraper.scrape("https://example.com")
        
        assert result.status_code == 200
        assert "Test" in result.html
        assert result.error is None

@pytest.mark.asyncio
async def test_scraper_404():
    """Test handling of 404 errors."""
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response
        
        scraper = WebScraper(respect_robots=False)
        result = await scraper.scrape("https://example.com/notfound")
        
        assert result.status_code == 404
        assert result.error is not None