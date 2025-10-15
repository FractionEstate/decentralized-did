"""
Tests for Input Sanitization Module

Tests all sanitizers for:
- HTML/script removal
- Unicode normalization
- Whitespace normalization
- Path traversal prevention
- Identifier sanitization
- Dictionary/list sanitization

License: Open-source (MIT)
"""

import pytest
from src.decentralized_did.api.sanitizers import (
    # HTML sanitization
    strip_html_tags,
    escape_html,
    remove_scripts,
    # Unicode sanitization
    normalize_unicode,
    remove_zero_width_chars,
    # Whitespace
    normalize_whitespace,
    limit_consecutive_spaces,
    # Path sanitization
    sanitize_path,
    # Identifier sanitization
    sanitize_identifier,
    sanitize_log_message,
    # Complex sanitization
    sanitize_dict,
    sanitize_list,
    sanitize_string,
    sanitize_for_json,
    # Helpers
    is_safe_string,
)


# ============================================================================
# HTML Sanitization Tests
# ============================================================================

class TestHTMLSanitization:
    """Tests for HTML sanitization"""
    
    def test_strip_html_tags(self):
        """Test HTML tag removal"""
        assert strip_html_tags("Hello <b>world</b>") == "Hello world"
        assert strip_html_tags("<p>Test</p>") == "Test"
        assert strip_html_tags("<div><span>Nested</span></div>") == "Nested"
    
    def test_strip_script_tags(self):
        """Test script tag removal"""
        assert strip_html_tags("<script>alert('xss')</script>") == ""
        assert strip_html_tags("Before<script>alert('xss')</script>After") == "BeforeAfter"
    
    def test_escape_html(self):
        """Test HTML escaping"""
        assert escape_html("<b>bold</b>") == "&lt;b&gt;bold&lt;/b&gt;"
        assert escape_html("'quote'") == "&#x27;quote&#x27;"
        assert escape_html("&<>") == "&amp;&lt;&gt;"
    
    def test_remove_scripts(self):
        """Test script removal"""
        assert remove_scripts("<script>alert(1)</script>") == ""
        assert remove_scripts("<SCRIPT>alert(1)</SCRIPT>") == ""
        assert remove_scripts("text<script>bad</script>more") == "textmore"


# ============================================================================
# Unicode Normalization Tests
# ============================================================================

class TestUnicodeNormalization:
    """Tests for Unicode normalization"""
    
    def test_normalize_unicode_nfkc(self):
        """Test NFKC normalization"""
        # é can be single char (U+00E9) or e + combining accent (U+0065 + U+0301)
        text1 = "café"  # Single char é
        text2 = "cafe\u0301"  # e + combining accent
        
        normalized1 = normalize_unicode(text1, form='NFKC')
        normalized2 = normalize_unicode(text2, form='NFKC')
        
        # Both should normalize to same form
        assert normalized1 == normalized2
    
    def test_remove_zero_width_chars(self):
        """Test zero-width character removal"""
        # Zero-width space (U+200B)
        assert remove_zero_width_chars("hello\u200bworld") == "helloworld"
        
        # Zero-width non-joiner (U+200C)
        assert remove_zero_width_chars("test\u200cvalue") == "testvalue"
        
        # Multiple zero-width chars
        assert remove_zero_width_chars("a\u200b\u200c\u200db") == "ab"


# ============================================================================
# Whitespace Normalization Tests
# ============================================================================

class TestWhitespaceNormalization:
    """Tests for whitespace normalization"""
    
    def test_normalize_whitespace_default(self):
        """Test default whitespace normalization"""
        assert normalize_whitespace("  hello    world  ") == "hello world"
        assert normalize_whitespace("test\r\n\rvalue") == "test\n\nvalue"
    
    def test_normalize_whitespace_no_collapse(self):
        """Test whitespace normalization without collapsing"""
        result = normalize_whitespace("hello    world", collapse_spaces=False, trim=True)
        assert result == "hello    world"
    
    def test_normalize_whitespace_no_trim(self):
        """Test whitespace normalization without trimming"""
        result = normalize_whitespace("  hello  ", collapse_spaces=False, trim=False)
        assert result == "  hello  "
    
    def test_limit_consecutive_spaces(self):
        """Test limiting consecutive spaces"""
        assert limit_consecutive_spaces("a" + " " * 20 + "b", max_spaces=5) == "a" + " " * 5 + "b"
        assert limit_consecutive_spaces("normal  spacing", max_spaces=10) == "normal  spacing"


# ============================================================================
# Path Sanitization Tests
# ============================================================================

class TestPathSanitization:
    """Tests for path sanitization"""
    
    def test_sanitize_path_normal(self):
        """Test normal path sanitization"""
        assert sanitize_path("data/file.json") == "data/file.json"
        assert sanitize_path("subfolder/data.txt") == "subfolder/data.txt"
    
    def test_sanitize_path_traversal_blocked(self):
        """Test path traversal attempts blocked"""
        with pytest.raises(ValueError, match="traversal"):
            sanitize_path("../../etc/passwd")
        
        with pytest.raises(ValueError, match="traversal"):
            sanitize_path("..\\..\\windows\\system32")
    
    def test_sanitize_path_absolute_blocked(self):
        """Test absolute paths converted to relative"""
        assert sanitize_path("/etc/passwd") == "etc/passwd"
        assert sanitize_path("/usr/bin") == "usr/bin"
    
    def test_sanitize_path_backslash_normalized(self):
        """Test backslash normalization"""
        assert sanitize_path("folder\\file.txt") == "folder/file.txt"


# ============================================================================
# Identifier Sanitization Tests
# ============================================================================

class TestIdentifierSanitization:
    """Tests for identifier sanitization"""
    
    def test_sanitize_identifier_normal(self):
        """Test normal identifier sanitization"""
        assert sanitize_identifier("user_name_123") == "user_name_123"
        assert sanitize_identifier("key-id") == "key-id"
    
    def test_sanitize_identifier_remove_special_chars(self):
        """Test special character removal"""
        assert sanitize_identifier("user@#$name") == "username"
        assert sanitize_identifier("id!@#$%^&*()") == "id"
    
    def test_sanitize_identifier_length_limit(self):
        """Test identifier length limiting"""
        long_id = "a" * 200
        result = sanitize_identifier(long_id)
        assert len(result) == 128  # Max length
    
    def test_sanitize_log_message(self):
        """Test log message sanitization"""
        # Remove newlines
        assert sanitize_log_message("line1\nline2") == "line1 line2"
        assert sanitize_log_message("log\r\nentry") == "log  entry"
        
        # Limit length
        long_msg = "x" * 2000
        result = sanitize_log_message(long_msg)
        assert len(result) <= 1003  # 1000 + '...'


# ============================================================================
# Dictionary/List Sanitization Tests
# ============================================================================

class TestComplexSanitization:
    """Tests for dictionary and list sanitization"""
    
    def test_sanitize_dict_html(self):
        """Test dictionary sanitization with HTML"""
        data = {"name": "<b>John</b>", "age": 30}
        result = sanitize_dict(data)
        assert result == {"name": "John", "age": 30}
    
    def test_sanitize_dict_nested(self):
        """Test nested dictionary sanitization"""
        data = {
            "user": {
                "name": "<script>alert(1)</script>Test",
                "bio": "Hello   world"
            }
        }
        result = sanitize_dict(data)
        assert result["user"]["name"] == "Test"
        assert result["user"]["bio"] == "Hello world"
    
    def test_sanitize_list_html(self):
        """Test list sanitization with HTML"""
        data = ["<b>item1</b>", "<i>item2</i>", "item3"]
        result = sanitize_list(data)
        assert result == ["item1", "item2", "item3"]
    
    def test_sanitize_list_nested(self):
        """Test nested list sanitization"""
        data = [["<b>a</b>", "<i>b</i>"], ["c", "d"]]
        result = sanitize_list(data)
        assert result == [["a", "b"], ["c", "d"]]
    
    def test_sanitize_string_comprehensive(self):
        """Test comprehensive string sanitization"""
        text = "  <b>Hello</b>   world\u200b  "
        result = sanitize_string(text)
        assert result == "Hello world"
    
    def test_sanitize_for_json(self):
        """Test JSON sanitization"""
        data = {
            "text": "<script>alert(1)</script>Safe",
            "items": ["<b>a</b>", "<i>b</i>"]
        }
        result = sanitize_for_json(data)
        assert result["text"] == "Safe"
        assert result["items"] == ["a", "b"]


# ============================================================================
# Helper Function Tests
# ============================================================================

class TestHelperFunctions:
    """Tests for helper functions"""
    
    def test_is_safe_string_safe(self):
        """Test safe string detection"""
        assert is_safe_string("Hello world") is True
        assert is_safe_string("Test 123") is True
    
    def test_is_safe_string_with_scripts(self):
        """Test unsafe string detection (scripts)"""
        assert is_safe_string("<script>alert(1)</script>") is False
        assert is_safe_string("<SCRIPT>bad</SCRIPT>") is False
    
    def test_is_safe_string_with_html(self):
        """Test HTML detection (when not allowed)"""
        assert is_safe_string("<b>bold</b>", allow_html=False) is False
        assert is_safe_string("<b>bold</b>", allow_html=True) is True
    
    def test_is_safe_string_with_control_chars(self):
        """Test control character detection"""
        assert is_safe_string("test\x00value") is False  # Null byte
        assert is_safe_string("test\x1fvalue") is False  # Unit separator


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and integration"""
    
    def test_sanitize_empty_string(self):
        """Test sanitizing empty string"""
        assert sanitize_string("") == ""
        assert strip_html_tags("") == ""
    
    def test_sanitize_none_values(self):
        """Test sanitizing None values"""
        assert sanitize_string(None) is None  # type: ignore
        assert strip_html_tags(123) == 123  # type: ignore
    
    def test_sanitize_unicode_mixed(self):
        """Test mixed Unicode sanitization"""
        text = "café\u200b  <b>test</b>  "
        result = sanitize_string(text)
        assert "test" in result
        assert "<b>" not in result
        assert "\u200b" not in result
    
    def test_sanitize_deeply_nested_dict(self):
        """Test deeply nested dictionary sanitization"""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "text": "<b>deep</b>"
                    }
                }
            }
        }
        result = sanitize_dict(data)
        assert result["level1"]["level2"]["level3"]["text"] == "deep"
    
    def test_sanitize_mixed_types(self):
        """Test sanitizing mixed types in dictionary"""
        data = {
            "string": "<b>text</b>",
            "number": 123,
            "boolean": True,
            "none": None,
            "list": ["<i>a</i>", 456]
        }
        result = sanitize_dict(data)
        assert result["string"] == "text"
        assert result["number"] == 123
        assert result["boolean"] is True
        assert result["none"] is None
        assert result["list"] == ["a", 456]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
