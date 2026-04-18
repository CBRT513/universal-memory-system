#!/usr/bin/env python3
"""
Test Firebase auth domain whitelisting
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from auth_integration import AuthIntegration, get_auth_integration


def test_authorized_domains():
    """Test that authorized domains are accepted"""
    print("\n=== Testing Authorized Domains ===")
    
    auth = get_auth_integration()
    
    # Test domains that should be allowed
    test_cases = [
        ("sso.test", True),
        ("cbrt-ui.test", True),
        ("localhost", True),
        ("http://localhost:5174", True),
        ("https://sso.test", True),
        ("http://cbrt-ui.test:3000", True),
        ("127.0.0.1", True),
        ("barge2rail.com", True),
        ("cbrt.com", True)
    ]
    
    passed = 0
    failed = 0
    
    for domain, should_allow in test_cases:
        result = auth.check_domain_whitelist(domain)
        is_allowed = result["allowed"]
        
        if is_allowed == should_allow:
            print(f"  ✓ {domain}: {'Allowed' if is_allowed else 'Blocked'} (as expected)")
            passed += 1
        else:
            print(f"  ✗ {domain}: {'Allowed' if is_allowed else 'Blocked'} (expected {'Allowed' if should_allow else 'Blocked'})")
            if "error" in result:
                print(f"    Error: {result['error']}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_unauthorized_domains():
    """Test that unauthorized domains are blocked"""
    print("\n=== Testing Unauthorized Domains ===")
    
    auth = get_auth_integration()
    
    # Test domains that should be blocked
    test_cases = [
        "evil.com",
        "http://malicious.site",
        "phishing.test",
        "unauthorized.domain"
    ]
    
    passed = 0
    failed = 0
    
    for domain in test_cases:
        result = auth.check_domain_whitelist(domain)
        
        if not result["allowed"]:
            print(f"  ✓ {domain}: Blocked correctly")
            print(f"    Error code: {result.get('code', 'N/A')}")
            passed += 1
        else:
            print(f"  ✗ {domain}: Allowed (should be blocked!)")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_error_handling():
    """Test graceful error handling"""
    print("\n=== Testing Error Handling ===")
    
    auth = get_auth_integration()
    
    # Test various error conditions
    test_cases = [
        (None, "No origin domain provided"),
        ("", "No origin domain provided"),
        ("http://", "Invalid domain format")
    ]
    
    passed = 0
    failed = 0
    
    for domain, expected_error_substring in test_cases:
        result = auth.check_domain_whitelist(domain)
        
        if not result["allowed"] and expected_error_substring in result.get("error", ""):
            print(f"  ✓ Input '{domain}': Handled gracefully")
            print(f"    Error: {result['error']}")
            passed += 1
        else:
            print(f"  ✗ Input '{domain}': Unexpected result")
            print(f"    Result: {result}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    return failed == 0


def test_validate_auth_request():
    """Test full auth request validation"""
    print("\n=== Testing Auth Request Validation ===")
    
    auth = get_auth_integration()
    
    # Test valid request
    valid_request = {
        "origin": "https://sso.test",
        "auth_method": "firebase",
        "email": "user@example.com"
    }
    
    result = auth.validate_auth_request(valid_request)
    if result["valid"]:
        print(f"  ✓ Valid request accepted")
        print(f"    Domain: {result.get('domain')}")
        print(f"    Method: {result.get('auth_method')}")
    else:
        print(f"  ✗ Valid request rejected: {result.get('error')}")
        return False
    
    # Test invalid domain
    invalid_request = {
        "origin": "https://hacker.com",
        "auth_method": "firebase"
    }
    
    result = auth.validate_auth_request(invalid_request)
    if not result["valid"] and result.get("code") == "auth/unauthorized-domain":
        print(f"  ✓ Invalid domain blocked correctly")
        print(f"    Error: {result.get('error')}")
    else:
        print(f"  ✗ Invalid domain not blocked properly")
        return False
    
    # Test invalid auth method
    bad_method_request = {
        "origin": "https://sso.test",
        "auth_method": "fake"
    }
    
    result = auth.validate_auth_request(bad_method_request)
    if not result["valid"] and result.get("code") == "auth/invalid-method":
        print(f"  ✓ Invalid auth method rejected")
    else:
        print(f"  ✗ Invalid auth method not rejected")
        return False
    
    print("\n✓ All auth request validations passed")
    return True


def test_error_message_handling():
    """Test Firebase error message handling"""
    print("\n=== Testing Error Message Handling ===")
    
    auth = get_auth_integration()
    
    # Simulate various Firebase errors
    test_errors = [
        (Exception("auth/unauthorized-domain"), {"domain": "evil.com"}),
        (Exception("auth/invalid-email"), {}),
        (Exception("auth/user-not-found"), {}),
        (Exception("auth/wrong-password"), {}),
        (Exception("unknown error"), {})
    ]
    
    for error, context in test_errors:
        result = auth.handle_auth_error(error, context)
        print(f"  Error: {str(error)[:30]}...")
        print(f"    → Code: {result.get('code')}")
        print(f"    → Message: {result.get('message', 'N/A')[:50]}...")
    
    print("\n✓ All error messages handled gracefully")
    return True


def test_domain_management():
    """Test runtime domain management"""
    print("\n=== Testing Domain Management ===")
    
    auth = get_auth_integration()
    
    # Get initial domains
    initial_domains = auth.get_authorized_domains()
    print(f"  Initial domains: {len(initial_domains)} authorized")
    
    # Add a new domain
    test_domain = "test.example.com"
    added = auth.add_domain(test_domain)
    if added:
        print(f"  ✓ Added domain: {test_domain}")
    else:
        print(f"  ✗ Failed to add domain: {test_domain}")
        return False
    
    # Verify it's in the list
    if test_domain in auth.get_authorized_domains():
        print(f"  ✓ Domain appears in authorized list")
    else:
        print(f"  ✗ Domain not in authorized list")
        return False
    
    # Test that it's now allowed
    result = auth.check_domain_whitelist(test_domain)
    if result["allowed"]:
        print(f"  ✓ New domain is authorized")
    else:
        print(f"  ✗ New domain not authorized")
        return False
    
    # Remove the domain
    removed = auth.remove_domain(test_domain)
    if removed:
        print(f"  ✓ Removed domain: {test_domain}")
    else:
        print(f"  ✗ Failed to remove domain")
        return False
    
    # Verify it's no longer allowed
    result = auth.check_domain_whitelist(test_domain)
    if not result["allowed"]:
        print(f"  ✓ Removed domain is now blocked")
    else:
        print(f"  ✗ Removed domain still authorized")
        return False
    
    print("\n✓ Domain management functions correctly")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("FIREBASE AUTH DOMAIN TESTS")
    print("=" * 60)
    
    # Run all tests
    results = []
    results.append(("Authorized Domains", test_authorized_domains()))
    results.append(("Unauthorized Domains", test_unauthorized_domains()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Auth Request Validation", test_validate_auth_request()))
    results.append(("Error Messages", test_error_message_handling()))
    results.append(("Domain Management", test_domain_management()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\nALL TESTS PASSED ✓")
    else:
        print("\nSOME TESTS FAILED ✗")
        sys.exit(1)