"""
Security utilities for preventing prompt injection and input sanitization.
"""
import re
import logging
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Known prompt injection patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?|commands?)",
    r"(system|user|assistant):\s*",
    r"<\|.*?\|>",  # Special tokens
    r"###?\s*(system|user|assistant|instruction)",
    r"(forget|ignore)\s+(everything|all|that)",
    r"pretend\s+(to\s+be|you\s+are)",
    r"act\s+as\s+(if\s+you\s+are\s+)?a?\s*",
    r"roleplay\s+as",
    r"access\s+(to\s+)?(private|confidential|restricted)",
    r"simulate\s+(being\s+)?a?\s*",
    r"you\s+are\s+now\s+(a\s+)?",
    r"new\s+(role|character|persona)",
    r"\\n\\n(system|user|assistant):",
    r"(\[|\()?system(\]|\))?:",
    r"jailbreak",
    r"developer\s+mode",
    r"godmode",
]

# Maximum lengths for different inputs
MAX_QUESTION_LENGTH = 500
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MAX_DURATION_HOURS = 8.0
MIN_DURATION_HOURS = 0.25

class SecurityResult(BaseModel):
    """Result of security validation."""
    is_safe: bool
    cleaned_input: str
    risk_score: float
    detected_patterns: List[str]
    warnings: List[str]

def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by removing potentially dangerous content.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove null bytes and control characters except whitespace
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r ')
    
    # Replace null bytes specifically
    text = text.replace('\x00', '')
    
    # Normalize whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip()
        logger.warning(f"Input truncated to {max_length} characters")
    
    return text

def detect_prompt_injection(text: str) -> SecurityResult:
    """
    Detect potential prompt injection attempts in user input.
    
    Args:
        text: User input to analyze
        
    Returns:
        SecurityResult with analysis results
    """
    if not text or not text.strip():
        return SecurityResult(
            is_safe=True,
            cleaned_input="",
            risk_score=0.0,
            detected_patterns=[],
            warnings=[]
        )
    
    text_lower = text.lower()
    detected_patterns = []
    warnings = []
    risk_score = 0.0
    
    # Check for known injection patterns
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE | re.MULTILINE):
            detected_patterns.append(pattern)
            risk_score += 0.3
    
    # Check for excessive special characters
    special_char_ratio = len(re.findall(r'[^\w\s]', text)) / max(len(text), 1)
    if special_char_ratio > 0.4:
        warnings.append("High ratio of special characters")
        risk_score += 0.2
    
    # Check for repeated patterns (possible injection attempts)
    if re.search(r'(.{10,})\1{2,}', text):
        warnings.append("Repeated text patterns detected")
        risk_score += 0.1
    
    # Check for suspicious keywords related to AI manipulation
    ai_manipulation_keywords = [
        'token', 'embedding', 'vector', 'model', 'training', 'dataset',
        'neural', 'transformer', 'gpt', 'llm', 'prompt', 'fine-tune'
    ]
    
    for keyword in ai_manipulation_keywords:
        if keyword in text_lower:
            risk_score += 0.1
            warnings.append(f"AI-related keyword detected: {keyword}")
    
    # Check for attempts to inject system-level commands
    system_keywords = ['sudo', 'rm ', 'del ', 'format', 'exec', 'eval', 'import']
    for keyword in system_keywords:
        if keyword in text_lower:
            risk_score += 0.4
            warnings.append(f"System command keyword detected: {keyword}")
    
    # Clean the input
    cleaned_input = sanitize_input(text, MAX_QUESTION_LENGTH)
    
    # Cap risk score at 1.0
    risk_score = min(risk_score, 1.0)
    
    # Consider high risk if score > 0.5 or specific patterns detected
    is_safe = risk_score <= 0.5 and not any([
        'ignore' in text_lower and 'instruction' in text_lower,
        'system:' in text_lower,
        'user:' in text_lower,
        'assistant:' in text_lower
    ])
    
    if not is_safe:
        logger.warning(f"Potential prompt injection detected: {detected_patterns}, risk_score: {risk_score}")
    
    return SecurityResult(
        is_safe=is_safe,
        cleaned_input=cleaned_input,
        risk_score=risk_score,
        detected_patterns=detected_patterns,
        warnings=warnings
    )

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid format
    """
    if not email or len(email) > MAX_EMAIL_LENGTH:
        return False
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def validate_name(name: str) -> bool:
    """
    Validate name format.
    
    Args:
        name: Name to validate
        
    Returns:
        True if name is valid format
    """
    if not name or len(name) > MAX_NAME_LENGTH:
        return False
    
    # Allow letters (including international), spaces, hyphens, apostrophes, and dots
    name_pattern = r"^[\w\s\-'.]+$"
    return bool(re.match(name_pattern, name))

def validate_duration(duration_str: str) -> tuple[bool, float]:
    """
    Validate and parse interview duration input.
    Accepts decimal numbers with either . or , as separator.
    
    Args:
        duration_str: Duration string to validate (e.g., "1.5", "1,5", "2")
        
    Returns:
        Tuple of (is_valid, parsed_duration_hours)
    """
    if not duration_str or not duration_str.strip():
        return False, 0.0
    
    # Clean and normalize the input
    duration_str = duration_str.strip()
    
    # Replace comma with dot for decimal parsing
    normalized = duration_str.replace(',', '.')
    
    try:
        duration = float(normalized)
        
        # Check bounds
        if duration < MIN_DURATION_HOURS or duration > MAX_DURATION_HOURS:
            return False, 0.0
            
        return True, duration
        
    except (ValueError, TypeError):
        return False, 0.0