"""
Web Scraper Module

Safe and polite web scraping with rate limiting, timeout enforcement,
and respectful crawling practices.

Author: Email Extraction System
"""

import asyncio
import aiohttp
import time
import random
from typing import Optional, Dict, List
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class ScrapedContent:
    """Container for scraped web content."""
    url: str
    html: str
    status_code: int
    headers: Dict[str, str]
    scraped_at: datetime
    response_time: float  # in seconds
    error: Optional[str] = None


class RateLimiter:
    """
    Rate limiter to enforce delays between requests to the same domain.
    """
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 5.0):
        """
        Initialize rate limiter.
        
        Args:
            min_delay: Minimum delay between requests (seconds)
            max_delay: Maximum delay between requests (seconds)
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time: Dict[str, float] = {}
    
    async def wait(self, domain: str):
        """
        Wait appropriate amount of time before making request to domain.
        
        Args:
            domain: Domain name to rate limit
        """
        current_time = time.time()
        
        if domain in self.last_request_time:
            elapsed = current_time - self.last_request_time[domain]
            required_delay = self.min_delay
            
            if elapsed < required_delay:
                wait_time = required_delay - elapsed
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s for {domain}")
                await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()


class RobotsChecker:
    """
    Checks robots.txt compliance for websites.
    """
    
    def __init__(self, user_agent: str = "*"):
        """
        Initialize robots.txt checker.
        
        Args:
            user_agent: User agent string to check against
        """
        self.user_agent = user_agent
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.cache_timeout = timedelta(hours=24)
        self.cache_time: Dict[str, datetime] = {}
    
    async def can_fetch(self, url: str, session: aiohttp.ClientSession) -> bool:
        """
        Check if URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            session: aiohttp session for making request
            
        Returns:
            True if URL can be fetched
        """
        try:
            parsed = urlparse(url)
            domain = f"{parsed.scheme}://{parsed.netloc}"
            robots_url = urljoin(domain, '/robots.txt')
            
            # Check cache
            if domain in self.robots_cache:
                # Check if cache is still valid
                if (domain in self.cache_time and 
                    datetime.now() - self.cache_time[domain] < self.cache_timeout):
                    parser = self.robots_cache[domain]
                    return parser.can_fetch(self.user_agent, url)
            
            # Fetch robots.txt
            parser = RobotFileParser()
            parser.set_url(robots_url)
            
            try:
                async with session.get(robots_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        # Parse robots.txt content
                        parser.parse(content.splitlines())
                        
                        # Cache the parser
                        self.robots_cache[domain] = parser
                        self.cache_time[domain] = datetime.now()
                        
                        return parser.can_fetch(self.user_agent, url)
                    else:
                        # No robots.txt or error - allow by default
                        logger.debug(f"No robots.txt found for {domain}, allowing access")
                        return True
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout fetching robots.txt for {domain}")
                return True  # Allow on timeout
            except Exception as e:
                logger.warning(f"Error fetching robots.txt for {domain}: {str(e)}")
                return True  # Allow on error
                
        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {str(e)}")
            return True  # Allow on error
    
    def get_crawl_delay(self, domain: str) -> Optional[float]:
        """
        Get the crawl delay specified in robots.txt.
        
        Args:
            domain: Domain to check
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        if domain in self.robots_cache:
            parser = self.robots_cache[domain]
            delay = parser.crawl_delay(self.user_agent)
            return float(delay) if delay else None
        return None


class WebScraper:
    """
    Safe and polite web scraper with rate limiting and respect for robots.txt.
    """
    
    def __init__(self,
                 user_agent: str = "EmailExtractionBot/1.0 (Internal Use)",
                 timeout: int = 30,
                 max_retries: int = 3,
                 rate_limit_delay: float = 1.0,
                 respect_robots: bool = True,
                 max_page_size: int = 10 * 1024 * 1024):  # 10MB
        """
        Initialize web scraper.
        
        Args:
            user_agent: User agent string
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            rate_limit_delay: Minimum delay between requests (seconds)
            respect_robots: Whether to respect robots.txt
            max_page_size: Maximum page size to download (bytes)
        """
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        ]
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_page_size = max_page_size
        self.respect_robots = respect_robots
        
        self.rate_limiter = RateLimiter(min_delay=rate_limit_delay)
        # Use a random user agent for the robots checker as well
        self.robots_checker = RobotsChecker(user_agent=random.choice(self.user_agents))
        
        # Statistics
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_bytes_downloaded = 0
    
    async def scrape(self, url: str) -> ScrapedContent:
        """
        Scrape a single URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedContent object with results
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Rate limiting
        await self.rate_limiter.wait(domain)
        
        # Create session with custom settings
        timeout_obj = aiohttp.ClientTimeout(total=self.timeout)
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        async with aiohttp.ClientSession(timeout=timeout_obj, headers=headers) as session:
            # Check robots.txt
            if self.respect_robots:
                can_fetch = await self.robots_checker.can_fetch(url, session)
                if not can_fetch:
                    logger.warning(f"Blocked by robots.txt: {url}")
                    return ScrapedContent(
                        url=url,
                        html="",
                        status_code=403,
                        headers={},
                        scraped_at=datetime.now(),
                        response_time=0.0,
                        error="Blocked by robots.txt"
                    )
                
                # Apply crawl delay from robots.txt if specified
                crawl_delay = self.robots_checker.get_crawl_delay(domain)
                if crawl_delay:
                    logger.debug(f"Applying crawl delay of {crawl_delay}s for {domain}")
                    await asyncio.sleep(crawl_delay)
            
            # Attempt to scrape with retries
            for attempt in range(self.max_retries):
                try:
                    start_time = time.time()
                    
                    async with session.get(url, allow_redirects=True) as response:
                        # Check content length before downloading
                        content_length = response.headers.get('Content-Length')
                        if content_length and int(content_length) > self.max_page_size:
                            logger.warning(f"Page too large: {url} ({content_length} bytes)")
                            return ScrapedContent(
                                url=url,
                                html="",
                                status_code=response.status,
                                headers=dict(response.headers),
                                scraped_at=datetime.now(),
                                response_time=time.time() - start_time,
                                error=f"Page size exceeds limit ({content_length} bytes)"
                            )
                        
                        # Download content with size limit
                        chunks = []
                        total_size = 0
                        
                        async for chunk in response.content.iter_chunked(8192):
                            total_size += len(chunk)
                            if total_size > self.max_page_size:
                                logger.warning(f"Page size limit exceeded for {url}")
                                return ScrapedContent(
                                    url=url,
                                    html="",
                                    status_code=response.status,
                                    headers=dict(response.headers),
                                    scraped_at=datetime.now(),
                                    response_time=time.time() - start_time,
                                    error=f"Page size exceeds limit (>{self.max_page_size} bytes)"
                                )
                            chunks.append(chunk)
                        
                        html = b''.join(chunks).decode('utf-8', errors='ignore')
                        response_time = time.time() - start_time
                        
                        # Update statistics
                        self.total_requests += 1
                        self.total_bytes_downloaded += total_size
                        
                        if response.status == 200:
                            self.successful_requests += 1
                            logger.info(f"Successfully scraped {url} ({total_size} bytes, {response_time:.2f}s)")
                        else:
                            self.failed_requests += 1
                            logger.warning(f"Non-200 status for {url}: {response.status}")
                        
                        return ScrapedContent(
                            url=url,
                            html=html,
                            status_code=response.status,
                            headers=dict(response.headers),
                            scraped_at=datetime.now(),
                            response_time=response_time,
                            error=None if response.status == 200 else f"HTTP {response.status}"
                        )
                
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout scraping {url} (attempt {attempt + 1}/{self.max_retries})")
                    if attempt == self.max_retries - 1:
                        self.total_requests += 1
                        self.failed_requests += 1
                        return ScrapedContent(
                            url=url,
                            html="",
                            status_code=0,
                            headers={},
                            scraped_at=datetime.now(),
                            response_time=0.0,
                            error="Request timeout"
                        )
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
                except aiohttp.ClientError as e:
                    logger.error(f"Client error scraping {url}: {str(e)} (attempt {attempt + 1}/{self.max_retries})")
                    if attempt == self.max_retries - 1:
                        self.total_requests += 1
                        self.failed_requests += 1
                        return ScrapedContent(
                            url=url,
                            html="",
                            status_code=0,
                            headers={},
                            scraped_at=datetime.now(),
                            response_time=0.0,
                            error=f"Client error: {str(e)}"
                        )
                    await asyncio.sleep(2 ** attempt)
                
                except Exception as e:
                    logger.error(f"Unexpected error scraping {url}: {str(e)} (attempt {attempt + 1}/{self.max_retries})")
                    if attempt == self.max_retries - 1:
                        self.total_requests += 1
                        self.failed_requests += 1
                        return ScrapedContent(
                            url=url,
                            html="",
                            status_code=0,
                            headers={},
                            scraped_at=datetime.now(),
                            response_time=0.0,
                            error=f"Unexpected error: {str(e)}"
                        )
                    await asyncio.sleep(2 ** attempt)
    
    async def scrape_multiple(self, urls: List[str], max_concurrent: int = 5) -> List[ScrapedContent]:
        """
        Scrape multiple URLs with concurrency control.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum number of concurrent requests
            
        Returns:
            List of ScrapedContent objects
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> ScrapedContent:
            async with semaphore:
                return await self.scrape(url)
        
        logger.info(f"Starting batch scrape of {len(urls)} URLs (max concurrent: {max_concurrent})")
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks)
        logger.info(f"Completed batch scrape: {self.successful_requests} successful, {self.failed_requests} failed")
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        Get scraping statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': (self.successful_requests / self.total_requests * 100) 
                          if self.total_requests > 0 else 0,
            'total_bytes_downloaded': self.total_bytes_downloaded,
            'total_mb_downloaded': self.total_bytes_downloaded / (1024 * 1024),
        }
    
    def reset_statistics(self):
        """Reset all statistics counters."""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.total_bytes_downloaded = 0


# Convenience function for simple scraping
async def scrape_url(url: str, **kwargs) -> ScrapedContent:
    """
    Convenience function to scrape a single URL.
    
    Args:
        url: URL to scrape
        **kwargs: Additional arguments for WebScraper
        
    Returns:
        ScrapedContent object
    """
    scraper = WebScraper(**kwargs)
    return await scraper.scrape(url)