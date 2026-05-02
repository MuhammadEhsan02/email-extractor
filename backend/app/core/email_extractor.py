"""
Email Extractor Module

Extracts and validates email addresses from text using regex patterns
and various validation rules. Filters out junk and invalid emails.
Includes de-obfuscation for common anti-scraping techniques.

Author: Email Extraction System
"""

import re
from typing import List, Set, Dict, Optional
from dataclasses import dataclass, field
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


@dataclass
class ContactInfo:
    """Container for all contacts extracted from text."""
    emails: List[EmailInfo]
    phone_numbers: List[str]
    social_links: Dict[str, str] = field(default_factory=dict)


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

    # Standard international/local phone number pattern
    PHONE_PATTERN = re.compile(
        r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}',
        re.IGNORECASE
    )

    # Social media domains to extract
    SOCIAL_PATTERN = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?(facebook\.com|twitter\.com|x\.com|instagram\.com|linkedin\.com|wa\.me)\/[A-Za-z0-9_.-]+',
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

    def extract(self, text: str, html_content: Optional[str] = None) -> ContactInfo:
        """
        Main extraction method.
        1. Clean and de-obfuscate text.
        2. Run Regex for emails and phones.
        3. Validate and Score results.
        """
        if not text and not html_content:
            return ContactInfo(emails=[], phone_numbers=[])

        text_to_process = text or ""
        # --- STEP 1: De-obfuscation ---
        # Convert "name [at] domain [dot] com" -> "name@domain.com"
        clean_text = self._deobfuscate(text_to_process)

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

        # Check HTML for mailto: links specifically
        if html_content:
            mailto_matches = re.finditer(r'href="mailto:([^"\'\?]+)', html_content, re.IGNORECASE)
            for match in mailto_matches:
                email_str = match.group(1).lower().strip()
                if self.remove_duplicates and email_str in seen_emails:
                    continue
                if self._is_junk(email_str) or not self.EMAIL_PATTERN.match(email_str):
                    continue
                try:
                    username, domain = email_str.split('@', 1)
                    info = EmailInfo(
                        email=email_str,
                        username=username,
                        domain=domain,
                        source_context="Extracted from mailto link",
                        confidence_score=1.0  # High confidence for mailto links
                    )
                    candidates.append(info)
                    seen_emails.add(email_str)
                except ValueError:
                    pass

        # --- STEP 3: Phone Regex Matching ---
        raw_phones = self.PHONE_PATTERN.finditer(clean_text)
        phones = []
        seen_phones = set()

        for match in raw_phones:
            phone_str = match.group(0).strip()
            
            # Simple validation to avoid matching purely random IDs (must have enough digits)
            # Remove all non-digit characters for length check
            digits_only = re.sub(r'\D', '', phone_str)
            if len(digits_only) < 8 or len(digits_only) > 15:
                continue
                
            if phone_str not in seen_phones:
                phones.append(phone_str)
                seen_phones.add(phone_str)

        # --- STEP 4: Social Media Links ---
        social_links = {}
        target_text_for_social = html_content if html_content else clean_text
        social_matches = self.SOCIAL_PATTERN.finditer(target_text_for_social)
        
        for match in social_matches:
            url = match.group(0)
            domain = match.group(1).lower()
            
            # Ensure it's a full URL
            if not url.startswith('http'):
                url = 'https://' + url
                
            # Map domain to standard keys
            key = domain.replace('.com', '')
            if key == 'x': key = 'twitter'
            if key == 'wa.me': key = 'whatsapp'
            
            if key not in social_links:
                social_links[key] = url

        return ContactInfo(emails=candidates, phone_numbers=phones, social_links=social_links)

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