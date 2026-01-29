"""
Email Extractor Module

Extracts and validates email addresses from text using regex patterns
and various validation rules. Filters out junk and invalid emails.
Includes de-obfuscation for common anti-scraping techniques.

Author: Email Extraction System
"""

import re
from typing import List, Set, Dict, Optional
from dataclasses import dataclass
from collections import Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmailInfo:
    """Container for email information."""
    email: str
    domain: str
    username: str
    is_valid: bool = True
    confidence_score: float = 1.0
    source_context: Optional[str] = None


class EmailExtractor:
    """
    Extracts and validates email addresses from text.
    Includes smart de-obfuscation logic.
    """
    
    # Comprehensive email regex pattern (RFC 5322 simplified)
    EMAIL_PATTERN = re.compile(
        r'\b[A-Za-z0-9]'  # Must start with alphanumeric
        r'[A-Za-z0-9._%+-]*'  # Can contain these characters
        r'@'  # Must have @
        r'[A-Za-z0-9]'  # Domain must start with alphanumeric
        r'[A-Za-z0-9.-]*'  # Domain can contain these
        r'\.[A-Za-z]{2,}'  # Must end with TLD (2+ chars)
        r'\b',
        re.IGNORECASE
    )

    # Common junk patterns to filter out
    JUNK_DOMAINS = {
        'example.com', 'test.com', 'domain.com', 'email.com', 
        'yourdomain.com', 'site.com', 'company.com'
    }
    
    # Files that look like emails (e.g. script.js, image.png)
    JUNK_EXTENSIONS = {
        'png', 'jpg', 'jpeg', 'gif', 'css', 'js', 'svg', 'woff', 'ttf', 'eot', 
        'mp4', 'mp3', 'wav', 'pdf', 'zip', 'rar', 'exe', 'iso'
    }

    def __init__(self, min_confidence: float = 0.0, remove_duplicates: bool = True):
        self.min_confidence = min_confidence
        self.remove_duplicates = remove_duplicates

    def extract(self, text: str) -> List[EmailInfo]:
        """
        Main extraction method.
        1. Clean and de-obfuscate text.
        2. Run Regex.
        3. Validate and Score results.
        """
        if not text:
            return []

        # --- STEP 1: De-obfuscation ---
        # Convert "name [at] domain [dot] com" -> "name@domain.com"
        clean_text = self._deobfuscate(text)

        # --- STEP 2: Regex Matching ---
        raw_matches = self.EMAIL_PATTERN.finditer(clean_text)
        
        candidates = []
        seen_emails = set()

        for match in raw_matches:
            email_str = match.group(0).lower()
            
            # Skip duplicates if requested
            if self.remove_duplicates and email_str in seen_emails:
                continue
                
            # Basic validation
            if self._is_junk(email_str):
                continue
                
            # Calculate Context (surrounding text)
            start, end = match.span()
            context_start = max(0, start - 30)
            context_end = min(len(clean_text), end + 30)
            context = clean_text[context_start:context_end].replace('\n', ' ').strip()
            
            # Create Info Object
            username, domain = email_str.split('@', 1)
            info = EmailInfo(
                email=email_str,
                username=username,
                domain=domain,
                source_context=f"...{context}...",
                confidence_score=self._calculate_confidence(email_str)
            )
            
            if info.confidence_score >= self.min_confidence:
                candidates.append(info)
                seen_emails.add(email_str)

        return candidates

    def _deobfuscate(self, text: str) -> str:
        """
        Fixes common email obfuscation patterns.
        """
        # 1. Replace [at], (at), {at}, <at>, " at " with "@"
        text = re.sub(r'\s*\[at\]\s*', '@', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(at\)\s*', '@', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+at\s+', '@', text, flags=re.IGNORECASE)
        
        # 2. Replace [dot], (dot), " dot " with "."
        text = re.sub(r'\s*\[dot\]\s*', '.', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(dot\)\s*', '.', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+dot\s+', '.', text, flags=re.IGNORECASE)
        
        return text

    def _is_junk(self, email: str) -> bool:
        """Returns True if email looks like a file or junk domain."""
        username, domain = email.split('@', 1)
        
        if domain in self.JUNK_DOMAINS:
            return True
            
        # Check for file extensions masquerading as domains (user@image.png)
        parts = domain.split('.')
        if len(parts) > 1 and parts[-1] in self.JUNK_EXTENSIONS:
            return True
            
        return False

    def _calculate_confidence(self, email: str) -> float:
        """
        Heuristic scoring.
        1.0 = Perfect business email
        0.5 = Generic/Free email
        """
        score = 1.0
        username, domain = email.split('@', 1)

        # Free providers get lower score
        if 'gmail' in domain or 'yahoo' in domain or 'hotmail' in domain:
            score -= 0.3
            
        # Short usernames might be junk
        if len(username) < 3:
            score -= 0.1
            
        return max(0.0, score)