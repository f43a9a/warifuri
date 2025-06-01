# GitHub Pages Deployment Troubleshooting

This document provides solutions for common GitHub Pages deployment issues in CI/CD workflows.

## Issue: "Cannot lock ref 'refs/heads/gh-pages'"

### Symptoms
- GitHub Actions workflow fails with git reference lock error
- Error message: `! [remote rejected] gh-pages -> gh-pages (cannot lock ref 'refs/heads/gh-pages': is at <sha> but expected <other-sha>)`
- Deployment action succeeds in build but fails during push

### Root Causes
1. **Force orphan conflicts**: Using `force_orphan: true` can create reference conflicts
2. **Concurrent deployments**: Multiple workflows trying to push to same branch
3. **Stale git references**: Cached refs pointing to non-existent commits
4. **Branch protection**: GitHub branch protection rules preventing force pushes

### Solutions

#### 1. Immediate Fix (Repository Admin)
```bash
# Option A: Delete gh-pages branch via GitHub web interface
# 1. Go to repository → Branches
# 2. Find gh-pages branch and delete it
# 3. Re-run the failed workflow

# Option B: Force reset via local git (requires push access)
./scripts/fix_gh_pages.sh --force-reset
```

#### 2. Workflow Configuration Fix
Update your `.github/workflows/docs.yml`:

```yaml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v4
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs/build/html
    publish_branch: gh-pages
    enable_jekyll: false
    user_name: 'github-actions[bot]'
    user_email: 'github-actions[bot]@users.noreply.github.com'
    commit_message: 'Deploy documentation ${{ github.sha }}'
    force_orphan: false  # ← Key: Set to false
    keep_files: false
```

#### 3. Concurrency Control
Add concurrency control to prevent conflicts:

```yaml
concurrency:
  group: "pages-${{ github.ref }}"
  cancel-in-progress: true
```

#### 4. Alternative: GitHub Pages Action (Native)
Use GitHub's official Pages action instead:

```yaml
- name: Setup Pages
  uses: actions/configure-pages@v3

- name: Upload artifact
  uses: actions/upload-pages-artifact@v2
  with:
    path: ./docs/build/html

- name: Deploy to GitHub Pages
  id: deployment
  uses: actions/deploy-pages@v2
```

### Best Practices

1. **Never use `force_orphan: true`** in production workflows
2. **Set proper concurrency controls** to prevent parallel deployments
3. **Use consistent commit authors** (github-actions bot)
4. **Enable `enable_jekyll: false`** for non-Jekyll sites
5. **Test deployment locally** before pushing to main

### Monitoring

To monitor deployment status:
```bash
# Check GitHub Pages deployment status
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/pages

# Check latest gh-pages commit
git ls-remote origin gh-pages
```

### Prevention

- Use branch protection rules to prevent force pushes
- Set up proper CI/CD environments with staging
- Use semantic versioning for documentation releases
- Implement proper rollback mechanisms

## Implementation in This Repository

This repository now uses the fixed configuration:
- ✅ Removed `force_orphan: true`
- ✅ Added proper git configuration
- ✅ Implemented concurrency control
- ✅ Added cleanup steps before deployment
- ✅ Provided manual fix script: `scripts/fix_gh_pages.sh`

The next GitHub Actions run should resolve the reference lock issue automatically.
