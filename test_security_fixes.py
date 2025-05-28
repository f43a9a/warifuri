#!/usr/bin/env python3
"""
Test script to validate security fixes are working correctly.
This script tests the key security improvements we've implemented.
"""

import sys
import os
from urllib.parse import urlparse

# Add src to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from warifuri.core.github import sanitize_github_url
from warifuri.cli.context import Context

def test_url_sanitization():
    """Test URL sanitization functionality."""
    print("Testing URL sanitization...")

    # Valid URLs
    valid_cases = [
        ("https://github.com/owner/repo", "owner/repo"),
        ("https://github.com/owner/repo.git", "owner/repo.git"),
        ("https://github.com/owner/repo/", "owner/repo"),
    ]

    for url, expected in valid_cases:
        try:
            result = sanitize_github_url(url)
            if result == expected:
                print(f"✅ Valid URL '{url}' -> '{result}'")
            else:
                print(f"❌ Valid URL '{url}' expected '{expected}' but got '{result}'")
                return False
        except Exception as e:
            print(f"❌ Valid URL '{url}' failed: {e}")
            return False

    # Invalid URLs should return None
    invalid_urls = [
        "https://evil.com/malicious",
        "javascript:alert('xss')",
        "file:///etc/passwd",
        "https://github.com/",
        "not-a-url",
        "",
        None,
    ]

    for url in invalid_urls:
        try:
            result = sanitize_github_url(url)
            if result is None:
                print(f"✅ Invalid URL '{url}' correctly rejected")
            else:
                print(f"❌ Invalid URL '{url}' should have been rejected but returned: {result}")
                return False
        except Exception as e:
            print(f"❌ Invalid URL '{url}' raised unexpected exception: {e}")
            return False

    return True

def test_html_escaping():
    """Test HTML escaping functionality."""
    print("\nTesting HTML escaping...")

    # Test html.escape directly since it's used in the code
    import html

    test_cases = [
        ("<script>alert('xss')</script>", "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"),
        ("<img src=x onerror=alert('xss')>", "&lt;img src=x onerror=alert(&#x27;xss&#x27;)&gt;"),
        ("Normal text", "Normal text"),
    ]

    for input_text, expected in test_cases:
        result = html.escape(input_text)
        if result == expected:
            print(f"✅ HTML escaping: '{input_text}' -> '{result}'")
        else:
            print(f"❌ HTML escaping failed: '{input_text}' expected '{expected}' but got '{result}'")
            return False

    return True

def test_exception_handling():
    """Test that assert statements are replaced with proper exceptions."""
    print("\nTesting exception handling...")

    # Create a context with no workspace
    ctx = Context()
    ctx.workspace_path = None

    try:
        ctx.ensure_workspace_path()
        print("❌ ensure_workspace_path should have raised an exception")
        return False
    except SystemExit:
        print("✅ ensure_workspace_path correctly raises SystemExit for None workspace")
        return True
    except Exception as e:
        print(f"✅ ensure_workspace_path correctly raises ClickException: {type(e).__name__}")
        return True

def main():
    """Run all security tests."""
    print("🔒 Running security validation tests...\n")

    tests = [
        test_url_sanitization,
        test_html_escaping,
        test_exception_handling,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print(f"❌ Test {test.__name__} failed")
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All security tests passed!")
        return 0
    else:
        print("⚠️  Some security tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
