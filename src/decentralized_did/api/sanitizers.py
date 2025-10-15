"""
Input Sanitization for API Servers

Provides sanitization utilities for:
- HTML/script injection prevention
- Unicode normalization
- Whitespace normalization
- Path traversal prevention
- SQL injection prevention (for logging)

License: Open-source (MIT)
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Union, Literal
from html import escape as html_escape


# ============================================================================
# Constants
# ============================================================================

# HTML tag pattern
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

# Script tag pattern (case-insensitive)
SCRIPT_PATTERN = re.compile(
    r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL)

# Path traversal patterns
PATH_TRAVERSAL_PATTERN = re.compile(r'\.\./|\.\.\\')

# SQL injection patterns (for logging only - we don't use SQL)
SQL_KEYWORDS = re.compile(
    r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b',
    re.IGNORECASE
)

# Control characters (except newline, tab, carriage return)
CONTROL_CHARS = re.compile(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]')

# Maximum consecutive whitespace
MAX_CONSECUTIVE_SPACES = 10


# ============================================================================
# HTML/Script Sanitization
# ============================================================================

def strip_html_tags(text: str) -> str:
    """
    Remove all HTML tags from text

    Args:
        text: Input text

    Returns:
        Text with HTML tags removed

    Examples:
        >>> strip_html_tags("Hello <b>world</b>")
        'Hello world'
        >>> strip_html_tags("<script>alert('xss')</script>")
        ''
    """
    if not isinstance(text, str):
        return text

    # Remove script tags first
    text = SCRIPT_PATTERN.sub('', text)

    # Remove all HTML tags
    text = HTML_TAG_PATTERN.sub('', text)

    return text


def escape_html(text: str) -> str:
    """
    Escape HTML special characters

    Args:
        text: Input text

    Returns:
        HTML-escaped text

    Examples:
        >>> escape_html("<script>alert('xss')</script>")
        '&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;'
    """
    if not isinstance(text, str):
        return text

    return html_escape(text, quote=True)


def remove_scripts(text: str) -> str:
    """
    Remove script tags and content

    Args:
        text: Input text

    Returns:
        Text with scripts removed
    """
    if not isinstance(text, str):
        return text

    return SCRIPT_PATTERN.sub('', text)


# ============================================================================
# Unicode Normalization
# ============================================================================

def normalize_unicode(
    text: str,
    form: Literal['NFC', 'NFKC', 'NFD', 'NFKD'] = 'NFKC',
    remove_control_chars: bool = True
) -> str:
    """
    Normalize Unicode text to prevent homograph attacks

    Args:
        text: Input text
        form: Unicode normalization form (NFC, NFKC, NFD, NFKD)
        remove_control_chars: Whether to remove control characters

    Returns:
        Normalized text

    Examples:
        >>> normalize_unicode("café")  # é could be single char or e+combining
        'café'  # normalized to single representation
    """
    if not isinstance(text, str):
        return text

    # Normalize Unicode
    normalized = unicodedata.normalize(form, text)

    # Remove control characters
    if remove_control_chars:
        normalized = CONTROL_CHARS.sub('', normalized)

    return normalized


def remove_zero_width_chars(text: str) -> str:
    """
    Remove zero-width Unicode characters (potential obfuscation)

    Args:
        text: Input text

    Returns:
        Text without zero-width characters

    Examples:
        >>> remove_zero_width_chars("hello\u200bworld")
        'helloworld'
    """
    if not isinstance(text, str):
        return text

    # Zero-width characters
    zero_width = [
        '\u200B',  # Zero-width space
        '\u200C',  # Zero-width non-joiner
        '\u200D',  # Zero-width joiner
        '\uFEFF',  # Zero-width no-break space
    ]

    for char in zero_width:
        text = text.replace(char, '')

    return text


# ============================================================================
# Whitespace Normalization
# ============================================================================

def normalize_whitespace(
    text: str,
    collapse_spaces: bool = True,
    trim: bool = True
) -> str:
    """
    Normalize whitespace in text

    Args:
        text: Input text
        collapse_spaces: Collapse consecutive spaces to single space
        trim: Remove leading/trailing whitespace

    Returns:
        Text with normalized whitespace

    Examples:
        >>> normalize_whitespace("hello    world  ")
        'hello world'
    """
    if not isinstance(text, str):
        return text

    # Trim leading/trailing whitespace
    if trim:
        text = text.strip()

    # Collapse consecutive spaces
    if collapse_spaces:
        text = re.sub(r' {2,}', ' ', text)

    # Normalize newlines
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    return text


def limit_consecutive_spaces(text: str, max_spaces: int = MAX_CONSECUTIVE_SPACES) -> str:
    """
    Limit consecutive spaces to prevent DoS

    Args:
        text: Input text
        max_spaces: Maximum consecutive spaces allowed

    Returns:
        Text with limited consecutive spaces
    """
    if not isinstance(text, str):
        return text

    pattern = r' {' + str(max_spaces + 1) + r',}'
    return re.sub(pattern, ' ' * max_spaces, text)


# ============================================================================
# Path Sanitization
# ============================================================================

def sanitize_path(path: str) -> str:
    """
    Sanitize file path to prevent directory traversal

    Args:
        path: File path

    Returns:
        Sanitized path

    Raises:
        ValueError: If path contains traversal attempts

    Examples:
        >>> sanitize_path("../../etc/passwd")
        Raises ValueError
        >>> sanitize_path("data/file.json")
        'data/file.json'
    """
    if not isinstance(path, str):
        raise ValueError("Path must be a string")

    # Check for path traversal
    if PATH_TRAVERSAL_PATTERN.search(path):
        raise ValueError("Path contains directory traversal attempt")

    # Remove leading slashes (prevent absolute paths)
    path = path.lstrip('/')

    # Normalize path separators
    path = path.replace('\\', '/')

    return path


# ============================================================================
# Identifier Sanitization
# ============================================================================

def sanitize_identifier(
    identifier: str,
    allow_chars: str = 'a-zA-Z0-9._-'
) -> str:
    """
    Sanitize identifier (usernames, key IDs, etc.)

    Args:
        identifier: Input identifier
        allow_chars: Regex character class of allowed characters

    Returns:
        Sanitized identifier

    Examples:
        >>> sanitize_identifier("user@#$name")
        'username'
        >>> sanitize_identifier("key-id_123")
        'key-id_123'
    """
    if not isinstance(identifier, str):
        return identifier

    # Remove disallowed characters
    pattern = f'[^{allow_chars}]'
    sanitized = re.sub(pattern, '', identifier)

    # Trim to reasonable length
    max_length = 128
    sanitized = sanitized[:max_length]

    return sanitized


def sanitize_log_message(message: str) -> str:
    """
    Sanitize log message to prevent log injection

    Args:
        message: Log message

    Returns:
        Sanitized message

    Examples:
        >>> sanitize_log_message("User login\\nADMIN: Backdoor")
        'User login ADMIN: Backdoor'
    """
    if not isinstance(message, str):
        return str(message)

    # Remove newlines (prevent log injection)
    message = message.replace('\n', ' ').replace('\r', ' ')

    # Escape special characters
    message = message.replace('\t', ' ')

    # Limit length
    max_length = 1000
    if len(message) > max_length:
        message = message[:max_length] + '...'

    return message


# ============================================================================
# Dictionary/JSON Sanitization
# ============================================================================

def sanitize_dict(
    obj: Dict[str, Any],
    strip_html: bool = True,
    do_normalize_unicode: bool = True,
    do_normalize_whitespace: bool = True
) -> Dict[str, Any]:
    """
    Recursively sanitize dictionary values

    Args:
        obj: Dictionary to sanitize
        strip_html: Whether to strip HTML tags
        do_normalize_unicode: Whether to normalize Unicode
        do_normalize_whitespace: Whether to normalize whitespace

    Returns:
        Sanitized dictionary

    Examples:
        >>> sanitize_dict({"name": "<b>John</b>", "age": 30})
        {'name': 'John', 'age': 30}
    """
    if not isinstance(obj, dict):
        return obj

    sanitized = {}
    for key, value in obj.items():
        # Sanitize key
        if isinstance(key, str):
            key = sanitize_string(
                key,
                strip_html=strip_html,
                do_normalize_unicode=do_normalize_unicode,
                do_normalize_whitespace=do_normalize_whitespace
            )

        # Sanitize value recursively
        if isinstance(value, str):
            value = sanitize_string(
                value,
                strip_html=strip_html,
                do_normalize_unicode=do_normalize_unicode,
                do_normalize_whitespace=do_normalize_whitespace
            )
        elif isinstance(value, dict):
            value = sanitize_dict(
                value,
                strip_html=strip_html,
                do_normalize_unicode=do_normalize_unicode,
                do_normalize_whitespace=do_normalize_whitespace
            )
        elif isinstance(value, list):
            value = sanitize_list(
                value,
                strip_html=strip_html,
                do_normalize_unicode=do_normalize_unicode,
                do_normalize_whitespace=do_normalize_whitespace
            )

        sanitized[key] = value

    return sanitized


def sanitize_list(
    lst: List[Any],
    strip_html: bool = True,
    do_normalize_unicode: bool = True,
    do_normalize_whitespace: bool = True
) -> List[Any]:
    """
    Recursively sanitize list items

    Args:
        lst: List to sanitize
        strip_html: Whether to strip HTML tags
        do_normalize_unicode: Whether to normalize Unicode
        do_normalize_whitespace: Whether to normalize whitespace

    Returns:
        Sanitized list
    """
    if not isinstance(lst, list):
        return lst

    sanitized = []
    for item in lst:
        if isinstance(item, str):
            item = sanitize_string(
                item,
                strip_html=strip_html,
                do_normalize_unicode=do_normalize_unicode,
                do_normalize_whitespace=do_normalize_whitespace
            )
        elif isinstance(item, dict):
            item = sanitize_dict(
                item,
                strip_html=strip_html,
                do_normalize_unicode=do_normalize_unicode,
                do_normalize_whitespace=do_normalize_whitespace
            )
        elif isinstance(item, list):
            item = sanitize_list(
                item,
                strip_html=strip_html,
                do_normalize_unicode=do_normalize_unicode,
                do_normalize_whitespace=do_normalize_whitespace
            )

        sanitized.append(item)

    return sanitized


def sanitize_string(
    text: str,
    strip_html: bool = True,
    do_normalize_unicode: bool = True,
    do_normalize_whitespace: bool = True,
    remove_zero_width: bool = True
) -> str:
    """
    Comprehensive string sanitization

    Args:
        text: Input text
        strip_html: Whether to strip HTML tags
        do_normalize_unicode: Whether to normalize Unicode
        do_normalize_whitespace: Whether to normalize whitespace
        remove_zero_width: Whether to remove zero-width characters

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return text

    # Strip HTML
    if strip_html:
        text = strip_html_tags(text)

    # Normalize Unicode
    if do_normalize_unicode:
        text = normalize_unicode(text)

    # Remove zero-width characters
    if remove_zero_width:
        text = remove_zero_width_chars(text)

    # Normalize whitespace
    if do_normalize_whitespace:
        text = normalize_whitespace(text)

    return text


# ============================================================================
# Helper Functions
# ============================================================================

def is_safe_string(text: str, allow_html: bool = False) -> bool:
    """
    Check if string is safe (no scripts, control chars, etc.)

    Args:
        text: Text to check
        allow_html: Whether to allow HTML tags (but not scripts)

    Returns:
        True if safe
    """
    if not isinstance(text, str):
        return False

    # Check for scripts
    if SCRIPT_PATTERN.search(text):
        return False

    # Check for control characters
    if CONTROL_CHARS.search(text):
        return False

    # Check for HTML (if not allowed)
    if not allow_html and HTML_TAG_PATTERN.search(text):
        return False

    return True


def sanitize_for_json(obj: Any) -> Any:
    """
    Sanitize object for safe JSON serialization

    Args:
        obj: Object to sanitize

    Returns:
        JSON-safe object
    """
    if isinstance(obj, dict):
        return sanitize_dict(obj)
    elif isinstance(obj, list):
        return sanitize_list(obj)
    elif isinstance(obj, str):
        return sanitize_string(obj)
    else:
        return obj
