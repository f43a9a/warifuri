#!/bin/bash
# Fix GitHub Pages branch reference lock issue
# This script helps resolve git reference conflicts in gh-pages branch

set -e

echo "🔧 Fixing GitHub Pages deployment issues..."

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if we have write access (indirectly by checking if we can create/delete branches)
echo "📋 Current git status:"
git status --porcelain

# Option 1: Clean local gh-pages reference
echo "🧹 Cleaning local gh-pages references..."
git branch -D gh-pages 2>/dev/null || echo "No local gh-pages branch to delete"

# Option 2: Force push a clean gh-pages branch (ONLY if you have admin access)
if [ "$1" = "--force-reset" ]; then
    echo "⚠️  WARNING: This will completely reset the gh-pages branch!"
    echo "💭 Creating orphan gh-pages branch..."

    # Create temporary orphan branch
    git checkout --orphan temp-gh-pages
    git rm -rf . 2>/dev/null || true
    echo "# GitHub Pages Placeholder" > README.md
    git add README.md
    git commit -m "Reset gh-pages branch"

    # Force push (WARNING: This deletes all gh-pages history)
    git push origin temp-gh-pages:gh-pages --force

    # Clean up
    git checkout main
    git branch -D temp-gh-pages

    echo "✅ gh-pages branch has been reset. GitHub Actions should now work."
else
    echo "💡 To completely reset gh-pages branch, run:"
    echo "   $0 --force-reset"
    echo ""
    echo "💡 Alternatively, ask repository admin to:"
    echo "   1. Delete gh-pages branch from GitHub web interface"
    echo "   2. Re-run GitHub Actions workflow"
fi

echo "✅ Local cleanup completed."
echo "🚀 Next GitHub Actions run should resolve the reference lock issue."
