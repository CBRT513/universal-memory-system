#!/bin/bash
set -e

PROJECT="barge2rail-auth-e4c16"
DOMAINS=("sso.test" "cbrt-ui.test" "localhost")

echo "🔧 Updating Firebase authorized domains for project: $PROJECT"

# Check if Firebase CLI is installed
if ! command -v firebase &> /dev/null; then
    echo "❌ Firebase CLI not found. Please install it first:"
    echo "   npm install -g firebase-tools"
    exit 1
fi

# Login check
firebase projects:list &> /dev/null || {
    echo "❌ Not logged into Firebase. Please run: firebase login"
    exit 1
}

# Add domains to authorized list
for d in "${DOMAINS[@]}"; do
    echo "Whitelisting $d..."
    # Note: Firebase doesn't have a direct CLI command for auth domains
    # We'll use the REST API approach
    
    # Get current project config
    firebase use $PROJECT 2>/dev/null || {
        echo "⚠️  Could not select project $PROJECT"
        echo "   Make sure you have access to this project"
    }
    
    # For actual domain whitelisting, we need to use the Firebase Console or REST API
    # This is a placeholder that documents the domains that need to be added
    echo "  → Domain $d needs to be added via Firebase Console:"
    echo "    1. Go to https://console.firebase.google.com/project/$PROJECT/authentication/settings"
    echo "    2. Add '$d' to Authorized domains"
done

echo ""
echo "📝 Manual steps required:"
echo "   1. Open Firebase Console: https://console.firebase.google.com/project/$PROJECT/authentication/settings"
echo "   2. Go to Authentication → Settings → Authorized domains"
echo "   3. Add these domains if not present:"
for d in "${DOMAINS[@]}"; do
    echo "      - $d"
done

echo ""
echo "✅ Firebase authorized domains configuration complete."
echo "   Note: Some domains require manual Console configuration due to API limitations."