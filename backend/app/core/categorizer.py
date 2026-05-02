"""
Categorizer Module

Optional AI/ML module for categorizing emails and websites.
Uses heuristics and optional AI for classification.

Author: Email Extraction System
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from collections import Counter
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Category:
    """Container for category information."""
    name: str
    confidence: float
    keywords_matched: List[str] = None
    
    def __post_init__(self):
        if self.keywords_matched is None:
            self.keywords_matched = []


class EmailCategorizer:
    """
    Categorizes emails and domains based on heuristics and patterns.
    Can be extended with AI/ML models.
    """
    
    # Category keywords (can be extended or loaded from config)
    CATEGORY_KEYWORDS = {
        'sales': {
            'keywords': ['sales', 'pricing', 'quote', 'purchase', 'buy', 'order', 
                        'commerce', 'shop', 'store', 'deals', 'offer'],
            'email_patterns': [r'sales@', r'shop@', r'order@', r'commerce@']
        },
        'support': {
            'keywords': ['support', 'help', 'service', 'assist', 'ticket', 
                        'helpdesk', 'customer', 'care'],
            'email_patterns': [r'support@', r'help@', r'service@', r'care@']
        },
        'marketing': {
            'keywords': ['marketing', 'newsletter', 'promo', 'campaign', 'advertise',
                        'media', 'pr', 'communications', 'brand'],
            'email_patterns': [r'marketing@', r'newsletter@', r'promo@', r'media@']
        },
        'hr': {
            'keywords': ['hr', 'human resources', 'recruitment', 'careers', 'jobs',
                        'hiring', 'talent', 'recruiting'],
            'email_patterns': [r'hr@', r'careers@', r'jobs@', r'recruiting@', r'talent@']
        },
        'tech': {
            'keywords': ['tech', 'it', 'development', 'engineering', 'developer',
                        'software', 'devops', 'sysadmin', 'infrastructure'],
            'email_patterns': [r'tech@', r'it@', r'dev@', r'engineering@']
        },
        'finance': {
            'keywords': ['finance', 'accounting', 'billing', 'payment', 'invoice',
                        'accounts', 'payable', 'receivable', 'treasury'],
            'email_patterns': [r'finance@', r'billing@', r'accounting@', r'ar@', r'ap@']
        },
        'legal': {
            'keywords': ['legal', 'compliance', 'privacy', 'gdpr', 'terms',
                        'lawyer', 'attorney', 'counsel'],
            'email_patterns': [r'legal@', r'compliance@', r'privacy@', r'counsel@']
        },
        'executive': {
            'keywords': ['ceo', 'cto', 'cfo', 'coo', 'executive', 'president',
                        'director', 'vp', 'vice president', 'chief'],
            'email_patterns': [r'ceo@', r'cto@', r'cfo@', r'president@']
        },
        'general': {
            'keywords': ['info', 'contact', 'general', 'inquiry', 'hello'],
            'email_patterns': [r'info@', r'contact@', r'hello@', r'general@']
        }
    }
    
    # Domain type indicators
    DOMAIN_TYPE_INDICATORS = {
        'ecommerce': ['shop', 'store', 'cart', 'buy', 'marketplace', 'retail'],
        'saas': ['app', 'platform', 'cloud', 'software', 'service', 'tool'],
        'agency': ['agency', 'studio', 'creative', 'design', 'marketing', 'digital'],
        'consulting': ['consulting', 'advisory', 'solutions', 'partners', 'group'],
        'education': ['edu', 'university', 'school', 'academy', 'learning', 'training'],
        'nonprofit': ['org', 'foundation', 'charity', 'nonprofit', 'ngo'],
        'government': ['gov', 'government', 'municipal', 'state', 'federal']
    }
    
    # Business type indicators for website text categorization
    BUSINESS_TYPES_KEYWORDS = {
        'bakery': ['bakery', 'baker', 'pastry', 'cake', 'bread', 'croissant', 'cookies', 'baking', 'patisserie'],
        'hotel': ['hotel', 'motel', 'resort', 'inn', 'hostel', 'suites', 'accommodation', 'booking', 'rooms'],
        'clothing': ['clothing', 'apparel', 'boutique', 'fashion', 'garment', 'dresses', 'menswear', 'womenswear', 'shirts'],
        'restaurant': ['restaurant', 'cafe', 'diner', 'menu', 'food', 'dining', 'kitchen', 'eatery', 'bistro'],
        'real_estate': ['real estate', 'realtor', 'property', 'properties', 'apartments', 'housing', 'mortgage', 'broker', 'listings'],
        'tech': ['software', 'technology', 'tech', 'app', 'platform', 'cloud', 'saas', 'development', 'it services'],
        'medical': ['clinic', 'hospital', 'medical', 'doctor', 'patient', 'health', 'healthcare', 'care', 'treatment'],
        'fitness': ['gym', 'fitness', 'workout', 'training', 'yoga', 'pilates', 'health club', 'exercise'],
        'manufacturing': ['manufacturing', 'industrial', 'steel plant', 'factory', 'production', 'machinery', 'assembly', 'plant'],
        'corporate': ['corporate', 'enterprise', 'holdings', 'group', 'corporation', 'inc', 'llc'],
        'ecommerce': ['e-commerce', 'ecommerce', 'online store', 'cart', 'checkout']
    }
    
    def __init__(self, 
                 use_ai: bool = False,
                 min_confidence: float = 0.5):
        """
        Initialize categorizer.
        
        Args:
            use_ai: Whether to use AI model for categorization (not implemented)
            min_confidence: Minimum confidence threshold
        """
        self.use_ai = use_ai
        self.min_confidence = min_confidence
        
        # Compile email patterns
        self.compiled_patterns = {}
        for category, data in self.CATEGORY_KEYWORDS.items():
            self.compiled_patterns[category] = [
                re.compile(pattern, re.IGNORECASE) 
                for pattern in data['email_patterns']
            ]
    
    def categorize_email(self, email: str, context: Optional[str] = None) -> List[Category]:
        """
        Categorize a single email address.
        
        Args:
            email: Email address to categorize
            context: Optional context text around the email
            
        Returns:
            List of Category objects (sorted by confidence)
        """
        categories = []
        email_lower = email.lower()
        
        # Check each category
        for category_name, data in self.CATEGORY_KEYWORDS.items():
            matched_keywords = []
            score = 0.0
            
            # Check email patterns
            for pattern in self.compiled_patterns[category_name]:
                if pattern.search(email_lower):
                    score += 0.8
                    matched_keywords.append(pattern.pattern)
            
            # Check keywords in email username
            username = email_lower.split('@')[0]
            for keyword in data['keywords']:
                if keyword in username:
                    score += 0.3
                    matched_keywords.append(keyword)
            
            # Check context if provided
            if context:
                context_lower = context.lower()
                for keyword in data['keywords']:
                    if keyword in context_lower:
                        score += 0.1
                        if keyword not in matched_keywords:
                            matched_keywords.append(keyword)
            
            # Normalize score to 0-1 range
            confidence = min(score, 1.0)
            
            # Add category if meets threshold
            if confidence >= self.min_confidence:
                categories.append(Category(
                    name=category_name,
                    confidence=confidence,
                    keywords_matched=matched_keywords
                ))
        
        # Sort by confidence
        categories.sort(key=lambda x: x.confidence, reverse=True)
        
        if categories:
            logger.debug(f"Categorized {email}: {categories[0].name} ({categories[0].confidence:.2f})")
        else:
            logger.debug(f"No category found for {email}")
        
        return categories
    
    def categorize_domain(self, domain: str, website_text: Optional[str] = None) -> List[Category]:
        """
        Categorize a domain/website.
        
        Args:
            domain: Domain name
            website_text: Optional text content from website
            
        Returns:
            List of Category objects
        """
        categories = []
        domain_lower = domain.lower()
        
        # Check domain type indicators
        for domain_type, keywords in self.DOMAIN_TYPE_INDICATORS.items():
            matched_keywords = []
            score = 0.0
            
            # Check domain name
            for keyword in keywords:
                if keyword in domain_lower:
                    score += 0.5
                    matched_keywords.append(keyword)
            
            # Check website text if provided
            if website_text:
                text_lower = website_text.lower()[:5000]  # Only check first 5000 chars
                keyword_count = sum(1 for keyword in keywords if keyword in text_lower)
                score += min(keyword_count * 0.1, 0.5)
                matched_keywords.extend([k for k in keywords if k in text_lower])
            
            # Normalize score
            confidence = min(score, 1.0)
            
            # Add category if meets threshold
            if confidence >= self.min_confidence:
                categories.append(Category(
                    name=domain_type,
                    confidence=confidence,
                    keywords_matched=list(set(matched_keywords))
                ))
        
        # Sort by confidence
        categories.sort(key=lambda x: x.confidence, reverse=True)
        
        return categories
    
    def predict_business_type(self, website_text: str) -> str:
        """
        Scan parsed HTML text to predict business type.
        Returns the most likely business label or 'unknown' if none found.
        """
        if not website_text:
            return 'unknown'
            
        text_lower = website_text.lower()
        best_score = 0
        best_label = 'unknown'
        
        # Categories that should carry more weight to override generic labels
        high_weight_categories = {'manufacturing', 'corporate', 'ecommerce'}
        
        for category, keywords in self.BUSINESS_TYPES_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                # Use regex strictly to find word boundaries for accuracy
                pattern = r'\b' + re.escape(keyword) + r'\b'
                score += len(re.findall(pattern, text_lower))
                
            if category in high_weight_categories:
                score *= 3  # Apply multiplier to high-weight categories
                
            if score > best_score:
                best_score = score
                best_label = category
                
        if best_score > 0:
            return best_label
        return 'unknown'
    
    def batch_categorize(self, emails: List[str]) -> Dict[str, List[Category]]:
        """
        Categorize multiple emails.
        
        Args:
            emails: List of email addresses
            
        Returns:
            Dictionary mapping emails to category lists
        """
        results = {}
        
        for email in emails:
            categories = self.categorize_email(email)
            results[email] = categories
        
        logger.info(f"Categorized {len(emails)} emails")
        return results
    
    def get_category_distribution(self, emails: List[str]) -> Dict[str, int]:
        """
        Get distribution of categories across emails.
        
        Args:
            emails: List of email addresses
            
        Returns:
            Dictionary with category counts
        """
        category_counts = Counter()
        
        for email in emails:
            categories = self.categorize_email(email)
            if categories:
                # Count the top category for each email
                category_counts[categories[0].name] += 1
        
        return dict(category_counts)
    
    def filter_by_category(self, 
                          emails: List[str], 
                          target_categories: Set[str],
                          min_confidence: Optional[float] = None) -> List[str]:
        """
        Filter emails by category.
        
        Args:
            emails: List of email addresses
            target_categories: Set of category names to include
            min_confidence: Minimum confidence (overrides instance default)
            
        Returns:
            Filtered list of emails
        """
        filtered = []
        confidence_threshold = min_confidence or self.min_confidence
        
        for email in emails:
            categories = self.categorize_email(email)
            
            # Check if any category matches target with sufficient confidence
            for category in categories:
                if (category.name in target_categories and 
                    category.confidence >= confidence_threshold):
                    filtered.append(email)
                    break
        
        logger.info(f"Filtered to {len(filtered)} emails in categories: {target_categories}")
        return filtered
    
    def suggest_contact_person(self, email: str) -> str:
        """
        Suggest what type of person this email likely represents.
        
        Args:
            email: Email address
            
        Returns:
            Description of likely contact person
        """
        categories = self.categorize_email(email)
        
        if not categories:
            return "General contact"
        
        top_category = categories[0]
        
        # Map categories to person types
        person_types = {
            'sales': 'Sales representative',
            'support': 'Customer support representative',
            'marketing': 'Marketing professional',
            'hr': 'HR/Recruitment specialist',
            'tech': 'Technical contact',
            'finance': 'Finance/Accounting contact',
            'legal': 'Legal/Compliance officer',
            'executive': 'Executive/Leadership',
            'general': 'General inquiry contact'
        }
        
        return person_types.get(top_category.name, 'General contact')
    
    def get_primary_category(self, email: str) -> Optional[str]:
        """
        Get the primary (highest confidence) category for an email.
        
        Args:
            email: Email address
            
        Returns:
            Category name or None
        """
        categories = self.categorize_email(email)
        return categories[0].name if categories else None


class AIEmailCategorizer(EmailCategorizer):
    """
    Extended categorizer with AI/ML capabilities (placeholder for future implementation).
    """
    
    def __init__(self, model_path: Optional[str] = None, **kwargs):
        """
        Initialize AI-powered categorizer.
        
        Args:
            model_path: Path to trained model (not implemented)
            **kwargs: Additional arguments for base categorizer
        """
        super().__init__(use_ai=True, **kwargs)
        self.model_path = model_path
        self.model = None
        
        logger.warning("AI categorization not yet implemented, using heuristics")
    
    def train_model(self, training_data: List[Dict]):
        """
        Train categorization model (not implemented).
        
        Args:
            training_data: Training examples
        """
        logger.warning("Model training not implemented")
        pass
    
    def predict_with_ai(self, email: str, context: Optional[str] = None) -> List[Category]:
        """
        Use AI model for prediction (not implemented, falls back to heuristics).
        
        Args:
            email: Email address
            context: Optional context
            
        Returns:
            List of Category objects
        """
        # Fallback to heuristic categorization
        return self.categorize_email(email, context)


# Convenience function
def categorize_email(email: str, context: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get primary category of an email.
    
    Args:
        email: Email address
        context: Optional context
        
    Returns:
        Primary category name or None
    """
    categorizer = EmailCategorizer()
    return categorizer.get_primary_category(email)