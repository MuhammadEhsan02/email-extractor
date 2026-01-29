"""
HTML Parser Module

Parses HTML content and extracts clean, visible text.
Removes scripts, styles, and other non-content elements.

Author: Email Extraction System
"""

from bs4 import BeautifulSoup, Tag, NavigableString
from typing import List, Dict, Optional, Set
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParsedContent:
    """Container for parsed HTML content."""
    text: str
    title: Optional[str] = None
    meta_description: Optional[str] = None
    links: List[str] = None
    headings: List[str] = None
    word_count: int = 0
    
    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.headings is None:
            self.headings = []
        if self.word_count == 0 and self.text:
            self.word_count = len(self.text.split())


class HTMLParser:
    """
    Parses HTML and extracts clean, visible text content.
    """
    
    # HTML tags to completely remove (along with their content)
    REMOVE_TAGS = [
        'script', 'style', 'noscript', 'iframe', 'embed',
        'object', 'applet', 'audio', 'video', 'canvas',
        'svg', 'math'
    ]
    
    # HTML tags that typically contain navigation/UI elements
    NAV_TAGS = [
        'nav', 'header', 'footer', 'aside', 'menu'
    ]
    
    # Meta tags to extract
    META_TAGS = [
        'description', 'keywords', 'author', 'og:description'
    ]
    
    def __init__(self,
                 remove_nav: bool = True,
                 extract_links: bool = True,
                 extract_headings: bool = True,
                 min_text_length: int = 10,
                 preserve_line_breaks: bool = True):
        """
        Initialize HTML parser.
        
        Args:
            remove_nav: Remove navigation elements
            extract_links: Extract all links from HTML
            extract_headings: Extract heading text
            min_text_length: Minimum text length to consider valid
            preserve_line_breaks: Preserve paragraph breaks in text
        """
        self.remove_nav = remove_nav
        self.extract_links = extract_links
        self.extract_headings = extract_headings
        self.min_text_length = min_text_length
        self.preserve_line_breaks = preserve_line_breaks
    
    def parse(self, html: str, base_url: Optional[str] = None) -> ParsedContent:
        """
        Parse HTML and extract clean text content.
        
        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links
            
        Returns:
            ParsedContent object with extracted information
        """
        if not html or not isinstance(html, str):
            logger.warning("Invalid or empty HTML provided")
            return ParsedContent(text="")
        
        try:
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract metadata
            title = self._extract_title(soup)
            meta_description = self._extract_meta_description(soup)
            
            # Extract links if requested
            links = []
            if self.extract_links:
                links = self._extract_links(soup, base_url)
            
            # Extract headings if requested
            headings = []
            if self.extract_headings:
                headings = self._extract_headings(soup)
            
            # Remove unwanted tags
            self._remove_unwanted_tags(soup)
            
            # Extract clean text
            text = self._extract_text(soup)
            
            # Clean and normalize text
            text = self._clean_text(text)
            
            result = ParsedContent(
                text=text,
                title=title,
                meta_description=meta_description,
                links=links,
                headings=headings
            )
            
            logger.info(f"Parsed HTML: {result.word_count} words, {len(links)} links, {len(headings)} headings")
            return result
            
        except Exception as e:
            logger.error(f"Error parsing HTML: {str(e)}")
            return ParsedContent(text="", title=None, meta_description=None)
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract page title.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Page title or None
        """
        try:
            # Try standard title tag
            title_tag = soup.find('title')
            if title_tag and title_tag.string:
                return title_tag.string.strip()
            
            # Try Open Graph title
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                return og_title['content'].strip()
            
            # Try h1 as fallback
            h1_tag = soup.find('h1')
            if h1_tag and h1_tag.string:
                return h1_tag.string.strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting title: {str(e)}")
            return None
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract meta description.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Meta description or None
        """
        try:
            # Try standard meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc['content'].strip()
            
            # Try Open Graph description
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content'):
                return og_desc['content'].strip()
            
            return None
            
        except Exception as e:
            logger.debug(f"Error extracting meta description: {str(e)}")
            return None
    
    def _extract_links(self, soup: BeautifulSoup, base_url: Optional[str] = None) -> List[str]:
        """
        Extract all links from HTML.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            
        Returns:
            List of absolute URLs
        """
        links = []
        
        try:
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                
                # Skip empty, javascript, and anchor links
                if not href or href.startswith(('#', 'javascript:', 'mailto:')):
                    continue
                
                # Resolve relative URLs if base_url provided
                if base_url and not href.startswith(('http://', 'https://')):
                    from urllib.parse import urljoin
                    href = urljoin(base_url, href)
                
                links.append(href)
            
            # Remove duplicates while preserving order
            seen = set()
            unique_links = []
            for link in links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            
            return unique_links
            
        except Exception as e:
            logger.error(f"Error extracting links: {str(e)}")
            return []
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract all heading text (h1-h6).
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of heading texts
        """
        headings = []
        
        try:
            for level in range(1, 7):  # h1 to h6
                for heading in soup.find_all(f'h{level}'):
                    text = heading.get_text(strip=True)
                    if text and len(text) >= self.min_text_length:
                        headings.append(text)
            
            return headings
            
        except Exception as e:
            logger.error(f"Error extracting headings: {str(e)}")
            return []
    
    def _remove_unwanted_tags(self, soup: BeautifulSoup):
        """
        Remove unwanted HTML tags from soup.
        
        Args:
            soup: BeautifulSoup object (modified in place)
        """
        # Remove scripts, styles, etc.
        for tag_name in self.REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()
        
        # Remove navigation elements if requested
        if self.remove_nav:
            for tag_name in self.NAV_TAGS:
                for tag in soup.find_all(tag_name):
                    tag.decompose()
        
        # Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, NavigableString) 
                                     and str(text).strip().startswith('<!--')):
            comment.extract()
    
    def _extract_text(self, soup: BeautifulSoup) -> str:
        """
        Extract visible text from BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted text
        """
        if self.preserve_line_breaks:
            # Extract text preserving some structure
            text_parts = []
            
            for element in soup.descendants:
                if isinstance(element, NavigableString):
                    text = str(element).strip()
                    if text:
                        text_parts.append(text)
                elif element.name in ['p', 'div', 'br', 'li', 'tr']:
                    # Add line breaks for block elements
                    text_parts.append('\n')
            
            return ' '.join(text_parts)
        else:
            # Simple text extraction
            return soup.get_text(separator=' ', strip=True)
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize extracted text.
        
        Args:
            text: Raw extracted text
            
        Returns:
            Cleaned text
        """
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove common artifacts
        text = re.sub(r'\[\s*\]', '', text)  # Empty brackets
        text = re.sub(r'\(\s*\)', '', text)  # Empty parentheses
        
        return text
    
    def extract_specific_elements(self, html: str, css_selector: str) -> List[str]:
        """
        Extract text from specific HTML elements using CSS selector.
        
        Args:
            html: HTML content
            css_selector: CSS selector for elements to extract
            
        Returns:
            List of text content from matching elements
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            elements = soup.select(css_selector)
            
            texts = []
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) >= self.min_text_length:
                    texts.append(text)
            
            logger.info(f"Extracted {len(texts)} elements matching '{css_selector}'")
            return texts
            
        except Exception as e:
            logger.error(f"Error extracting elements with selector '{css_selector}': {str(e)}")
            return []
    
    def extract_structured_data(self, html: str) -> Dict:
        """
        Extract structured data (JSON-LD, microdata, etc.) from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Dictionary containing structured data
        """
        import json
        
        structured_data = {
            'json_ld': [],
            'meta_tags': {},
            'open_graph': {},
            'twitter_card': {}
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract JSON-LD
            for script in soup.find_all('script', type='application/ld+json'):
                try:
                    data = json.loads(script.string)
                    structured_data['json_ld'].append(data)
                except json.JSONDecodeError:
                    continue
            
            # Extract meta tags
            for meta in soup.find_all('meta'):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    if name.startswith('og:'):
                        structured_data['open_graph'][name] = content
                    elif name.startswith('twitter:'):
                        structured_data['twitter_card'][name] = content
                    else:
                        structured_data['meta_tags'][name] = content
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return structured_data
    
    def is_valid_content(self, parsed: ParsedContent) -> bool:
        """
        Check if parsed content meets minimum quality criteria.
        
        Args:
            parsed: ParsedContent object
            
        Returns:
            True if content is valid
        """
        # Must have some text
        if not parsed.text or len(parsed.text) < self.min_text_length:
            return False
        
        # Word count should be reasonable
        if parsed.word_count < 10:
            return False
        
        return True


# Convenience function for simple parsing
def parse_html(html: str, base_url: Optional[str] = None) -> ParsedContent:
    """
    Convenience function to parse HTML.
    
    Args:
        html: HTML content
        base_url: Base URL for resolving links
        
    Returns:
        ParsedContent object
    """
    parser = HTMLParser()
    return parser.parse(html, base_url)