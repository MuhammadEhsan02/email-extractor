"""
Limiter Module

Enforces limits on scraping operations including page count,
file size, request timeouts, and domain-level restrictions.

Author: Email Extraction System
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class LimitConfig:
    """Configuration for various limits."""
    max_pages_per_domain: int = 10
    max_total_pages: int = 50
    max_page_size_mb: float = 10.0
    max_total_size_mb: float = 100.0
    max_request_timeout_seconds: int = 30
    max_execution_time_minutes: int = 10
    max_concurrent_requests: int = 5
    min_request_delay_seconds: float = 1.0
    max_retry_attempts: int = 3


@dataclass
class DomainLimits:
    """Track limits for a specific domain."""
    domain: str
    pages_scraped: int = 0
    total_bytes: int = 0
    last_request_time: Optional[datetime] = None
    failed_requests: int = 0
    blocked: bool = False
    block_reason: Optional[str] = None


@dataclass
class SessionStats:
    """Statistics for the current scraping session."""
    start_time: datetime = field(default_factory=datetime.now)
    total_pages_scraped: int = 0
    total_bytes_downloaded: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    blocked_requests: int = 0
    domains_accessed: int = 0
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_elapsed_minutes(self) -> float:
        """Get elapsed time in minutes."""
        return self.get_elapsed_time() / 60.0


class LimitEnforcer:
    """
    Enforces various limits on web scraping operations.
    """
    
    def __init__(self, config: Optional[LimitConfig] = None):
        """
        Initialize limit enforcer.
        
        Args:
            config: LimitConfig object (uses defaults if not provided)
        """
        self.config = config or LimitConfig()
        self.domain_limits: Dict[str, DomainLimits] = {}
        self.stats = SessionStats()
        
        logger.info(f"Initialized LimitEnforcer with config: {self.config}")
    
    def can_scrape_url(self, url: str, domain: str) -> tuple[bool, Optional[str]]:
        """
        Check if URL can be scraped based on current limits.
        
        Args:
            url: URL to check
            domain: Domain of the URL
            
        Returns:
            Tuple of (can_scrape: bool, reason: Optional[str])
        """
        # Check total pages limit
        if self.stats.total_pages_scraped >= self.config.max_total_pages:
            return False, f"Total page limit reached ({self.config.max_total_pages})"
        
        # Check execution time limit
        if self.stats.get_elapsed_minutes() >= self.config.max_execution_time_minutes:
            return False, f"Execution time limit reached ({self.config.max_execution_time_minutes} minutes)"
        
        # Get or create domain limits
        if domain not in self.domain_limits:
            self.domain_limits[domain] = DomainLimits(domain=domain)
        
        domain_limit = self.domain_limits[domain]
        
        # Check if domain is blocked
        if domain_limit.blocked:
            return False, f"Domain blocked: {domain_limit.block_reason}"
        
        # Check per-domain page limit
        if domain_limit.pages_scraped >= self.config.max_pages_per_domain:
            return False, f"Domain page limit reached ({self.config.max_pages_per_domain} pages)"
        
        # Check rate limiting (time since last request)
        if domain_limit.last_request_time:
            time_since_last = (datetime.now() - domain_limit.last_request_time).total_seconds()
            if time_since_last < self.config.min_request_delay_seconds:
                return False, f"Rate limit: wait {self.config.min_request_delay_seconds - time_since_last:.1f}s"
        
        return True, None
    
    def can_download_size(self, size_bytes: int, domain: str) -> tuple[bool, Optional[str]]:
        """
        Check if downloading a file of given size is allowed.
        
        Args:
            size_bytes: Size in bytes
            domain: Domain of the file
            
        Returns:
            Tuple of (can_download: bool, reason: Optional[str])
        """
        size_mb = size_bytes / (1024 * 1024)
        
        # Check per-page size limit
        if size_mb > self.config.max_page_size_mb:
            return False, f"Page size ({size_mb:.2f}MB) exceeds limit ({self.config.max_page_size_mb}MB)"
        
        # Check total session size limit
        total_mb = self.stats.total_bytes_downloaded / (1024 * 1024)
        if total_mb + size_mb > self.config.max_total_size_mb:
            return False, f"Total size limit would be exceeded ({self.config.max_total_size_mb}MB)"
        
        # Check domain-specific size (optional additional check)
        if domain in self.domain_limits:
            domain_mb = self.domain_limits[domain].total_bytes / (1024 * 1024)
            # Allow up to 50% of total limit per domain
            domain_limit_mb = self.config.max_total_size_mb * 0.5
            if domain_mb + size_mb > domain_limit_mb:
                return False, f"Domain size limit would be exceeded ({domain_limit_mb}MB)"
        
        return True, None
    
    def record_request_start(self, domain: str):
        """
        Record the start of a request to a domain.
        
        Args:
            domain: Domain being requested
        """
        if domain not in self.domain_limits:
            self.domain_limits[domain] = DomainLimits(domain=domain)
        
        self.domain_limits[domain].last_request_time = datetime.now()
        
        # Count unique domains
        if self.domain_limits[domain].pages_scraped == 0:
            self.stats.domains_accessed += 1
    
    def record_success(self, domain: str, size_bytes: int):
        """
        Record a successful request.
        
        Args:
            domain: Domain that was scraped
            size_bytes: Size of downloaded content
        """
        if domain not in self.domain_limits:
            self.domain_limits[domain] = DomainLimits(domain=domain)
        
        # Update domain stats
        self.domain_limits[domain].pages_scraped += 1
        self.domain_limits[domain].total_bytes += size_bytes
        
        # Update session stats
        self.stats.total_pages_scraped += 1
        self.stats.total_bytes_downloaded += size_bytes
        self.stats.successful_requests += 1
        
        logger.debug(f"Recorded success for {domain}: {size_bytes} bytes "
                    f"(domain: {self.domain_limits[domain].pages_scraped} pages, "
                    f"total: {self.stats.total_pages_scraped} pages)")
    
    def record_failure(self, domain: str, reason: str):
        """
        Record a failed request.
        
        Args:
            domain: Domain that failed
            reason: Failure reason
        """
        if domain not in self.domain_limits:
            self.domain_limits[domain] = DomainLimits(domain=domain)
        
        # Update domain stats
        self.domain_limits[domain].failed_requests += 1
        
        # Update session stats
        self.stats.failed_requests += 1
        
        # Block domain if too many failures
        if self.domain_limits[domain].failed_requests >= self.config.max_retry_attempts:
            self.block_domain(domain, f"Too many failures ({self.domain_limits[domain].failed_requests})")
        
        logger.warning(f"Recorded failure for {domain}: {reason}")
    
    def record_blocked(self, domain: str, reason: str):
        """
        Record a blocked request.
        
        Args:
            domain: Domain that was blocked
            reason: Block reason
        """
        self.stats.blocked_requests += 1
        logger.info(f"Request blocked for {domain}: {reason}")
    
    def block_domain(self, domain: str, reason: str):
        """
        Block further requests to a domain.
        
        Args:
            domain: Domain to block
            reason: Reason for blocking
        """
        if domain not in self.domain_limits:
            self.domain_limits[domain] = DomainLimits(domain=domain)
        
        self.domain_limits[domain].blocked = True
        self.domain_limits[domain].block_reason = reason
        
        logger.warning(f"Blocked domain {domain}: {reason}")
    
    def unblock_domain(self, domain: str):
        """
        Unblock a domain.
        
        Args:
            domain: Domain to unblock
        """
        if domain in self.domain_limits:
            self.domain_limits[domain].blocked = False
            self.domain_limits[domain].block_reason = None
            logger.info(f"Unblocked domain {domain}")
    
    def get_domain_stats(self, domain: str) -> Optional[DomainLimits]:
        """
        Get statistics for a specific domain.
        
        Args:
            domain: Domain to query
            
        Returns:
            DomainLimits object or None
        """
        return self.domain_limits.get(domain)
    
    def get_session_stats(self) -> SessionStats:
        """
        Get current session statistics.
        
        Returns:
            SessionStats object
        """
        return self.stats
    
    def get_remaining_capacity(self) -> Dict:
        """
        Get remaining capacity for various limits.
        
        Returns:
            Dictionary with remaining capacity information
        """
        return {
            'pages_remaining': max(0, self.config.max_total_pages - self.stats.total_pages_scraped),
            'mb_remaining': max(0, self.config.max_total_size_mb - 
                              (self.stats.total_bytes_downloaded / (1024 * 1024))),
            'minutes_remaining': max(0, self.config.max_execution_time_minutes - 
                                   self.stats.get_elapsed_minutes()),
            'percent_pages_used': (self.stats.total_pages_scraped / self.config.max_total_pages) * 100,
            'percent_size_used': ((self.stats.total_bytes_downloaded / (1024 * 1024)) / 
                                 self.config.max_total_size_mb) * 100,
            'percent_time_used': (self.stats.get_elapsed_minutes() / 
                                 self.config.max_execution_time_minutes) * 100
        }
    
    def should_stop_session(self) -> tuple[bool, Optional[str]]:
        """
        Check if the session should be stopped based on limits.
        
        Returns:
            Tuple of (should_stop: bool, reason: Optional[str])
        """
        # Check total pages
        if self.stats.total_pages_scraped >= self.config.max_total_pages:
            return True, "Total page limit reached"
        
        # Check total size
        total_mb = self.stats.total_bytes_downloaded / (1024 * 1024)
        if total_mb >= self.config.max_total_size_mb:
            return True, "Total size limit reached"
        
        # Check execution time
        if self.stats.get_elapsed_minutes() >= self.config.max_execution_time_minutes:
            return True, "Execution time limit reached"
        
        # Check failure rate (stop if >80% failures)
        total_requests = self.stats.successful_requests + self.stats.failed_requests
        if total_requests >= 10:  # Only check after minimum requests
            failure_rate = self.stats.failed_requests / total_requests
            if failure_rate > 0.8:
                return True, f"High failure rate ({failure_rate*100:.1f}%)"
        
        return False, None
    
    def reset_session(self):
        """Reset session statistics and domain limits."""
        self.domain_limits.clear()
        self.stats = SessionStats()
        logger.info("Session statistics reset")
    
    def get_summary(self) -> Dict:
        """
        Get comprehensive summary of limits and statistics.
        
        Returns:
            Dictionary with summary information
        """
        return {
            'config': {
                'max_total_pages': self.config.max_total_pages,
                'max_pages_per_domain': self.config.max_pages_per_domain,
                'max_total_size_mb': self.config.max_total_size_mb,
                'max_execution_time_minutes': self.config.max_execution_time_minutes
            },
            'stats': {
                'elapsed_minutes': self.stats.get_elapsed_minutes(),
                'total_pages_scraped': self.stats.total_pages_scraped,
                'total_mb_downloaded': self.stats.total_bytes_downloaded / (1024 * 1024),
                'successful_requests': self.stats.successful_requests,
                'failed_requests': self.stats.failed_requests,
                'blocked_requests': self.stats.blocked_requests,
                'domains_accessed': self.stats.domains_accessed,
                'success_rate': (self.stats.successful_requests / 
                               max(1, self.stats.successful_requests + self.stats.failed_requests)) * 100
            },
            'capacity': self.get_remaining_capacity(),
            'domains': {
                domain: {
                    'pages': limits.pages_scraped,
                    'mb': limits.total_bytes / (1024 * 1024),
                    'failed': limits.failed_requests,
                    'blocked': limits.blocked
                }
                for domain, limits in self.domain_limits.items()
            }
        }


# Convenience function for creating standard limiter
def create_standard_limiter(**overrides) -> LimitEnforcer:
    """
    Create a LimitEnforcer with standard configuration.
    
    Args:
        **overrides: Config parameters to override
        
    Returns:
        LimitEnforcer instance
    """
    config = LimitConfig(**overrides)
    return LimitEnforcer(config)