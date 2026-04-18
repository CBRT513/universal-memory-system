# Firebase Auth Domain Authorization Fix

## Overview
This document describes the fix for Firebase `auth/unauthorized-domain` errors in the CBRT authentication system.

## Problem
Firebase Authentication blocks login attempts from domains not explicitly whitelisted in the Firebase Console, resulting in:
```
Error: auth/unauthorized-domain
This domain is not authorized for OAuth operations
```

## Solution
1. Backend domain validation before Firebase redirect
2. Graceful error handling for unauthorized domains
3. Manual Firebase Console configuration for production domains

## Manual Firebase Console Steps

### Required Steps
1. **Open Firebase Console**:
   ```
   https://console.firebase.google.com/project/barge2rail-auth-e4c16/authentication/settings
   ```

2. **Navigate to Authorized Domains**:
   - Go to Authentication → Settings
   - Find "Authorized domains" section

3. **Add Required Domains**:
   - `sso.test` - SSO test environment
   - `cbrt-ui.test` - CBRT UI test environment
   - `localhost` - Local development
   - Any production domains:
     - `barge2rail.com`
     - `cbrt.com`

### CLI Automation

Run the provided script to get instructions:
```bash
./scripts/fix_firebase_domains.sh
```

This script will:
- Check Firebase CLI installation
- Verify Firebase login status
- Provide manual steps for domain configuration
- Document which domains need to be added

### One-Liner for Domain Check
```bash
firebase --project barge2rail-auth-e4c16 auth:export - | grep -E "authorizedDomains|domain"
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Update Firebase Domains
on:
  push:
    paths:
      - 'config/firebase-domains.json'

jobs:
  update-domains:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: w9jds/firebase-action@master
        with:
          args: deploy --only hosting
        env:
          FIREBASE_TOKEN: ${{ secrets.FIREBASE_TOKEN }}
      - run: ./scripts/fix_firebase_domains.sh
```

### Environment Variables
```bash
# Optional: Add extra domains at runtime
export FIREBASE_EXTRA_DOMAINS="staging.cbrt.com,dev.barge2rail.com"

# Firebase project
export FIREBASE_PROJECT="barge2rail-auth-e4c16"
```

## Backend Integration

### Domain Validation
The `auth_integration.py` module provides:
- Pre-flight domain checking
- Graceful error responses
- Runtime domain management

### Usage Example
```python
from auth_integration import get_auth_integration

auth = get_auth_integration()

# Check if domain is authorized
result = auth.check_domain_whitelist("https://sso.test")
if result["allowed"]:
    # Proceed with Firebase auth
    pass
else:
    # Return controlled error
    return {
        "error": result["error"],
        "code": result["code"],
        "suggestion": "Please use an authorized domain"
    }
```

### Auth Request Validation
```python
# Validate full auth request
request = {
    "origin": "https://cbrt-ui.test",
    "auth_method": "firebase",
    "email": "user@example.com"
}

validation = auth.validate_auth_request(request)
if validation["valid"]:
    # Proceed with authentication
    pass
else:
    # Return error to client
    return validation
```

## Database Schema

### New Tables
- `auth_events` - Tracks all auth attempts and outcomes
- `authorized_domains` - Manages domain whitelist
- `auth_metrics` - View for auth statistics

### User Sessions Enhancement
Added columns:
- `auth_source` - Track auth method (firebase/sso/local)
- `auth_domain` - Track originating domain
- `auth_metadata` - Additional auth context

## Testing

### Run Tests
```bash
python3 tests/test_auth_domains.py
```

### Expected Results
- ✅ `sso.test` - Authorized
- ✅ `cbrt-ui.test` - Authorized
- ✅ `localhost:*` - Authorized (any port)
- ❌ Unknown domains - Controlled error response

## Troubleshooting

### Domain Still Blocked After Adding
1. Check Firebase Console - changes may take 1-2 minutes
2. Clear browser cache
3. Verify domain format (no trailing slashes)
4. Check for typos in domain name

### Getting Current Authorized Domains
```python
from auth_integration import get_auth_integration

auth = get_auth_integration()
domains = auth.get_authorized_domains()
print("Authorized domains:", domains)
```

### Debugging Auth Failures
Check auth events in database:
```sql
SELECT * FROM auth_events 
WHERE event_type = 'domain_blocked' 
ORDER BY occurred_at DESC 
LIMIT 10;
```

## Security Notes

1. **Never bypass domain validation** - It's a critical security feature
2. **Production domains** should be explicitly whitelisted
3. **Monitor auth_events** table for unauthorized access attempts
4. **Regular audits** of authorized_domains list

## Next Steps (D4 Prep)

1. **Production Domains**:
   - Add `barge2rail.com`
   - Add `cbrt.com`
   - Add any CDN/proxy domains

2. **Automation**:
   - Create Firebase Admin SDK script for programmatic updates
   - Add to deployment pipeline

3. **SSO Federation**:
   - Begin implementing cross-app SSO
   - Unified session management
   - Single sign-out capability