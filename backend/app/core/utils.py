"""
Utilities Module

Helper functions and utilities used across the system.

Author: Email Extraction System
"""

import re
import hashlib
import json
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# String Utilities
# ============================================================================

def clean_text(text: str, remove_extra_whitespace: bool = True) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Text to clean
        remove_extra_whitespace: Remove extra spaces and newlines
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    if remove_extra_whitespace:
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\s*\n+', '\n\n', text)
    
    # Trim
    text = text.strip()
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize all whitespace to single spaces.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    return re.sub(r'\s+', ' ', text).strip()


# ============================================================================
# URL Utilities
# ============================================================================

def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid and well-formed.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except Exception:
        return False


def get_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL to parse
        
    Returns:
        Domain name or None
    """
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception as e:
        logger.debug(f"Error extracting domain from {url}: {str(e)}")
        return None


def get_base_domain(domain: str) -> str:
    """
    Get base domain (removing subdomains).
    
    Args:
        domain: Domain name
        
    Returns:
        Base domain
    """
    parts = domain.split('.')
    if len(parts) >= 2:
        return '.'.join(parts[-2:])
    return domain


def normalize_url(url: str) -> str:
    """
    Normalize URL (lowercase domain, remove trailing slash, etc.).
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    try:
        parsed = urlparse(url)
        
        # Normalize domain to lowercase
        netloc = parsed.netloc.lower()
        
        # Remove trailing slash from path
        path = parsed.path.rstrip('/')
        
        # Reconstruct
        normalized = f"{parsed.scheme}://{netloc}{path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        return normalized
    except Exception:
        return url


# ============================================================================
# File Utilities
# ============================================================================

def ensure_directory(path: str) -> str:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path
        
    Returns:
        Absolute path to directory
    """
    Path(path).mkdir(parents=True, exist_ok=True)
    return str(Path(path).absolute())


def get_file_size_mb(filepath: str) -> float:
    """
    Get file size in megabytes.
    
    Args:
        filepath: Path to file
        
    Returns:
        File size in MB
    """
    try:
        size_bytes = Path(filepath).stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception as e:
        logger.error(f"Error getting file size for {filepath}: {str(e)}")
        return 0.0


def get_safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Convert filename to safe format (remove invalid characters).
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        
    Returns:
        Safe filename
    """
    # Remove invalid characters
    safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    safe = safe.strip('. ')
    
    # Truncate if too long
    if len(safe) > max_length:
        name, ext = Path(safe).stem, Path(safe).suffix
        safe = name[:max_length - len(ext)] + ext
    
    return safe


def generate_unique_filename(base_path: str, extension: str = '') -> str:
    """
    Generate unique filename by adding timestamp.
    
    Args:
        base_path: Base filename/path
        extension: File extension (with or without dot)
        
    Returns:
        Unique filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    
    if not extension.startswith('.') and extension:
        extension = f'.{extension}'
    
    base = Path(base_path).stem
    directory = Path(base_path).parent
    
    filename = f"{base}_{timestamp}{extension}"
    return str(directory / filename)


# ============================================================================
# Data Utilities
# ============================================================================

def remove_duplicates(items: List[Any], key: Optional[callable] = None) -> List[Any]:
    """
    Remove duplicates from list while preserving order.
    
    Args:
        items: List of items
        key: Optional function to extract comparison key
        
    Returns:
        List without duplicates
    """
    seen = set()
    result = []
    
    for item in items:
        k = key(item) if key else item
        if k not in seen:
            seen.add(k)
            result.append(item)
    
    return result


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks.
    
    Args:
        items: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """
    Flatten nested list.
    
    Args:
        nested_list: Nested list
        
    Returns:
        Flattened list
    """
    return [item for sublist in nested_list for item in sublist]


# ============================================================================
# Hash Utilities
# ============================================================================

def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash of string.
    
    Args:
        text: Text to hash
        algorithm: Hash algorithm (md5, sha1, sha256, etc.)
        
    Returns:
        Hex digest of hash
    """
    h = hashlib.new(algorithm)
    h.update(text.encode('utf-8'))
    return h.hexdigest()


def hash_file(filepath: str, algorithm: str = 'sha256') -> str:
    """
    Generate hash of file contents.
    
    Args:
        filepath: Path to file
        algorithm: Hash algorithm
        
    Returns:
        Hex digest of hash
    """
    h = hashlib.new(algorithm)
    
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    
    return h.hexdigest()


# ============================================================================
# Validation Utilities
# ============================================================================

def is_valid_email_simple(email: str) -> bool:
    """
    Simple email validation (basic format check).
    
    Args:
        email: Email address
        
    Returns:
        True if appears valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_domain(domain: str) -> bool:
    """
    Check if domain name appears valid.
    
    Args:
        domain: Domain name
        
    Returns:
        True if appears valid
    """
    pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


# ============================================================================
# JSON Utilities
# ============================================================================

def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """
    Safely load JSON with default fallback.
    
    Args:
        json_string: JSON string
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.debug(f"JSON parse error: {str(e)}")
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Safely dump object to JSON.
    
    Args:
        obj: Object to serialize
        default: Default string if serialization fails
        
    Returns:
        JSON string
    """
    try:
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (TypeError, ValueError) as e:
        logger.debug(f"JSON dump error: {str(e)}")
        return default


# ============================================================================
# Time Utilities
# ============================================================================

def format_timestamp(dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime as string.
    
    Args:
        dt: Datetime object (uses current time if None)
        format_str: Format string
        
    Returns:
        Formatted timestamp
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse timestamp string to datetime.
    
    Args:
        timestamp_str: Timestamp string
        format_str: Format string
        
    Returns:
        Datetime object or None
    """
    try:
        return datetime.strptime(timestamp_str, format_str)
    except ValueError as e:
        logger.debug(f"Timestamp parse error: {str(e)}")
        return None


def get_elapsed_time_str(start_time: datetime, end_time: Optional[datetime] = None) -> str:
    """
    Get human-readable elapsed time.
    
    Args:
        start_time: Start datetime
        end_time: End datetime (uses current time if None)
        
    Returns:
        Formatted elapsed time string
    """
    if end_time is None:
        end_time = datetime.now()
    
    elapsed = end_time - start_time
    
    hours, remainder = divmod(elapsed.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if hours > 0:
        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
    elif minutes > 0:
        return f"{int(minutes)}m {int(seconds)}s"
    else:
        return f"{seconds:.1f}s"


# ============================================================================
# Statistics Utilities
# ============================================================================

def calculate_percentage(part: int, total: int, decimal_places: int = 2) -> float:
    """
    Calculate percentage.
    
    Args:
        part: Part value
        total: Total value
        decimal_places: Decimal places to round to
        
    Returns:
        Percentage value
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, decimal_places)


def get_summary_stats(numbers: List[float]) -> Dict[str, float]:
    """
    Get summary statistics for list of numbers.
    
    Args:
        numbers: List of numbers
        
    Returns:
        Dictionary with statistics
    """
    if not numbers:
        return {
            'count': 0,
            'min': 0,
            'max': 0,
            'mean': 0,
            'median': 0,
            'sum': 0
        }
    
    sorted_numbers = sorted(numbers)
    count = len(numbers)
    
    return {
        'count': count,
        'min': min(numbers),
        'max': max(numbers),
        'mean': sum(numbers) / count,
        'median': sorted_numbers[count // 2] if count % 2 == 1 else 
                 (sorted_numbers[count // 2 - 1] + sorted_numbers[count // 2]) / 2,
        'sum': sum(numbers)
    }


# ============================================================================
# Logging Utilities
# ============================================================================

def setup_logger(name: str, 
                log_file: Optional[str] = None, 
                level: int = logging.INFO,
                format_str: Optional[str] = None) -> logging.Logger:
    """
    Setup logger with file and console handlers.
    
    Args:
        name: Logger name
        log_file: Optional log file path
        level: Logging level
        format_str: Custom format string
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Default format
    if format_str is None:
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_str)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        ensure_directory(Path(log_file).parent)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# ============================================================================
# Configuration Utilities
# ============================================================================

def merge_configs(default_config: Dict, user_config: Dict) -> Dict:
    """
    Merge user config into default config.
    
    Args:
        default_config: Default configuration
        user_config: User configuration
        
    Returns:
        Merged configuration
    """
    merged = default_config.copy()
    
    for key, value in user_config.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged


def load_config_file(filepath: str) -> Dict:
    """
    Load configuration from JSON file.
    
    Args:
        filepath: Path to config file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load config from {filepath}: {str(e)}")
        return {}


def save_config_file(config: Dict, filepath: str):
    """
    Save configuration to JSON file.
    
    Args:
        config: Configuration dictionary
        filepath: Path to save to
    """
    try:
        ensure_directory(Path(filepath).parent)
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved configuration to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save config to {filepath}: {str(e)}")
        raise