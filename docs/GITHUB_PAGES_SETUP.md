# GitHub Pages Setup Guide

This document provides instructions for setting up GitHub Pages to host the warifuri documentation.

## Automatic Setup (Recommended)

GitHub Pages is configured to deploy automatically when code is pushed to the `main` branch. The documentation is built using Sphinx and deployed using GitHub Actions.

## Manual Setup Steps

If automatic deployment doesn't work, follow these manual steps:

### 1. Enable GitHub Pages

1. Go to your repository on GitHub
2. Click on **Settings** tab
3. Scroll down to **Pages** section
4. Under **Source**, select:
   - **Deploy from a branch**
   - Branch: `gh-pages`
   - Folder: `/ (root)`
5. Click **Save**

### 2. Verify Workflow Permissions

Ensure the repository has the correct workflow permissions:

1. Go to **Settings** > **Actions** > **General**
2. Under **Workflow permissions**, select:
   - ✅ **Read and write permissions**
   - ✅ **Allow GitHub Actions to create and approve pull requests**
3. Click **Save**

### 3. Enable GitHub Pages Environment

1. Go to **Settings** > **Environments**
2. If `github-pages` environment doesn't exist, create it:
   - Click **New environment**
   - Name: `github-pages`
   - Add deployment protection rules if needed
3. Ensure the environment is properly configured

## Alternative Deployment Methods

### Method 1: GitHub Actions with deploy-pages

Uses the official `actions/deploy-pages` action (default):

```yaml
# .github/workflows/docs.yml
- name: Deploy to GitHub Pages
  uses: actions/deploy-pages@v2
```

### Method 2: Third-party Action

Uses `peaceiris/actions-gh-pages` for more control:

```yaml
# .github/workflows/docs-alt.yml
- name: Deploy to GitHub Pages
  uses: peaceiris/actions-gh-pages@v3
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    publish_dir: ./docs/build/html
```

## Troubleshooting

### Common Issues

1. **"No Pages site found"**: Enable Pages in repository settings
2. **Workflow permissions error**: Update Actions permissions
3. **Build failures**: Check Python/Poetry setup in workflow
4. **404 errors**: Verify `index.html` exists in build output

### Debug Steps

1. Check workflow logs in **Actions** tab
2. Verify build artifacts contain HTML files
3. Test documentation builds locally:
   ```bash
   cd docs
   poetry run sphinx-build -b html source build/html
   ```

## Documentation URL

Once deployed, documentation will be available at:
- **Primary**: https://f43a9a.github.io/warifuri/
- **Alternative**: https://your-username.github.io/warifuri/

## File Structure

```
docs/
├── source/           # Sphinx source files
│   ├── conf.py      # Sphinx configuration
│   ├── index.rst    # Main documentation page
│   ├── api/         # Auto-generated API docs
│   └── user-guide/  # User documentation
└── build/           # Generated HTML (not in repo)
    └── html/        # Built documentation
```

## Updates

Documentation is automatically rebuilt and deployed when:
- Code is pushed to `main` branch
- Pull requests are merged
- Manual workflow dispatch is triggered

For manual builds, run:
```bash
poetry install --with docs
cd docs
poetry run sphinx-build -b html source build/html
```
