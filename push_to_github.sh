#!/bin/bash
# Script to push changes to GitHub

cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"

echo "📦 Checking git status..."
git status

echo ""
echo "📤 Pushing to GitHub..."
echo "Branch: feature/v2-deal-workspace"
echo ""

git push origin feature/v2-deal-workspace

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Successfully pushed to GitHub!"
    echo "🔗 View on GitHub: https://github.com/pinakiaich/vc-stack/tree/feature/v2-deal-workspace"
else
    echo ""
    echo "❌ Push failed. You may need to:"
    echo "   1. Enter your GitHub username and password/token"
    echo "   2. Or set up SSH keys for authentication"
    echo ""
    echo "Alternative: Use GitHub Desktop or push from your IDE"
fi
