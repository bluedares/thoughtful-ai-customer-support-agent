# Git Setup Guide

## Initial Setup

### 1. Initialize Git Repository

```bash
cd /Volumes/WorkSpace/Projects/InterviewPreps/ThoughfulAI
git init
```

### 2. Verify .gitignore

The `.gitignore` file is already configured to exclude sensitive files:

```bash
# View .gitignore
cat .gitignore
```

**Key exclusions**:
- ✅ `.env` - Environment variables (API keys)
- ✅ `.env.local` - Local environment overrides
- ✅ `.env.*.local` - Environment-specific files
- ✅ `chroma_db/` - Vector database (can be regenerated)
- ✅ `__pycache__/` - Python cache files
- ✅ `.venv/` - Virtual environment
- ✅ `.streamlit/secrets.toml` - Streamlit secrets

### 3. Verify No Sensitive Files

```bash
# Check what will be committed
git status

# Ensure .env is NOT listed
# If it appears, it means .gitignore isn't working
```

**If .env appears in git status**:
```bash
# Remove from git tracking (keeps local file)
git rm --cached .env

# Verify it's now ignored
git status
```

### 4. Add Files

```bash
# Add all files (respecting .gitignore)
git add .

# Verify .env is NOT added
git status
```

### 5. Initial Commit

```bash
git commit -m "Initial commit: Thoughtful AI Multi-Agent Support System

- Multi-agent architecture with LangGraph
- Claude Sonnet 4.5 integration
- ChromaDB vector store for RAG
- FastAPI backend with observability
- Streamlit frontend with debug panel
- Docker containerization
- Railway deployment configuration
- Comprehensive documentation"
```

## Create GitHub Repository

### Option 1: GitHub CLI

```bash
# Install GitHub CLI (if not installed)
brew install gh  # macOS
# or download from https://cli.github.com/

# Login
gh auth login

# Create repository
gh repo create thoughtful-ai-support \
  --public \
  --description "Multi-agent AI support system with LangGraph, Claude, and comprehensive observability" \
  --source=. \
  --remote=origin \
  --push
```

### Option 2: GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: `thoughtful-ai-support`
3. Description: "Multi-agent AI support system with LangGraph, Claude, and comprehensive observability"
4. Choose Public or Private
5. **Do NOT** initialize with README (we already have one)
6. Click "Create repository"

Then connect locally:
```bash
git remote add origin https://github.com/YOUR_USERNAME/thoughtful-ai-support.git
git branch -M main
git push -u origin main
```

## Branch Strategy

### Main Branch Protection

```bash
# Create development branch
git checkout -b develop

# Make changes on feature branches
git checkout -b feature/new-agent
# ... make changes ...
git add .
git commit -m "Add new agent"
git push origin feature/new-agent
```

### Recommended Branches

- `main` - Production-ready code
- `develop` - Development integration
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

## Commit Message Convention

Follow conventional commits:

```bash
# Format: <type>(<scope>): <subject>

# Types:
feat: New feature
fix: Bug fix
docs: Documentation changes
style: Code style changes (formatting)
refactor: Code refactoring
test: Adding tests
chore: Maintenance tasks

# Examples:
git commit -m "feat(rag): add similarity threshold configuration"
git commit -m "fix(router): handle edge case in classification"
git commit -m "docs: update API documentation"
git commit -m "refactor(agents): simplify state management"
```

## Common Git Workflows

### Daily Development

```bash
# Start of day - update from remote
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/improve-matching

# Make changes
# ... edit files ...

# Stage and commit
git add .
git commit -m "feat(rag): improve semantic matching accuracy"

# Push to remote
git push origin feature/improve-matching

# Create pull request on GitHub
```

### Update Knowledge Base

```bash
# Edit data/qa_dataset.json
vim data/qa_dataset.json

# Commit changes
git add data/qa_dataset.json
git commit -m "docs: update Q&A dataset with new questions"

# Push
git push origin main
```

### Fix Production Bug

```bash
# Create hotfix from main
git checkout main
git checkout -b hotfix/api-timeout

# Fix the bug
# ... edit files ...

# Commit
git add .
git commit -m "fix(api): increase timeout for LLM calls"

# Push and merge to main
git push origin hotfix/api-timeout
# Create PR and merge
```

## Security Best Practices

### 1. Never Commit Secrets

**Check before committing**:
```bash
# Search for potential secrets
git grep -i "api.key"
git grep -i "sk-ant"
git grep -i "password"

# If found, remove and use environment variables
```

### 2. Use .env for Secrets

```bash
# Good ✅
ANTHROPIC_API_KEY=sk-ant-...  # in .env (gitignored)

# Bad ❌
api_key = "sk-ant-..."  # in code (committed)
```

### 3. Verify .gitignore

```bash
# Test if .env would be ignored
git check-ignore .env
# Should output: .env

# If not ignored, add to .gitignore
echo ".env" >> .gitignore
```

### 4. Remove Accidentally Committed Secrets

If you accidentally committed a secret:

```bash
# Remove from git history (DANGER: rewrites history)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (only if repository is private and you're the only user)
git push origin --force --all

# IMPORTANT: Rotate the exposed secret immediately!
```

**Better approach**: Use BFG Repo-Cleaner:
```bash
# Install BFG
brew install bfg  # macOS

# Remove .env from history
bfg --delete-files .env

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push origin --force --all
```

## Git Hooks

### Pre-commit Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Check for secrets
if git diff --cached | grep -i "sk-ant"; then
    echo "❌ Error: API key detected in commit!"
    echo "Remove the API key and use environment variables."
    exit 1
fi

# Check for .env file
if git diff --cached --name-only | grep -q "^\.env$"; then
    echo "❌ Error: .env file in commit!"
    echo "This file should be gitignored."
    exit 1
fi

# Run tests (optional)
# python -m pytest tests/

echo "✅ Pre-commit checks passed"
exit 0
```

Make it executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Collaboration

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/thoughtful-ai-support.git
cd thoughtful-ai-support

# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env and add your API key
```

### Pull Request Workflow

1. **Fork** the repository (if external contributor)
2. **Clone** your fork
3. **Create branch** for your feature
4. **Make changes** and commit
5. **Push** to your fork
6. **Create PR** on GitHub
7. **Address review** comments
8. **Merge** when approved

### Code Review Checklist

- [ ] No secrets in code
- [ ] Tests pass
- [ ] Documentation updated
- [ ] Commit messages clear
- [ ] No merge conflicts
- [ ] .env.example updated if new variables added

## Deployment with Git

### Railway Auto-Deploy

Railway automatically deploys when you push to main:

```bash
# Make changes
git add .
git commit -m "feat: add new feature"

# Push to main
git push origin main

# Railway detects push and deploys automatically
```

### Manual Deploy Trigger

```bash
# Tag a release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# Railway can be configured to deploy on tags
```

## Troubleshooting

### Undo Last Commit

```bash
# Keep changes
git reset --soft HEAD~1

# Discard changes
git reset --hard HEAD~1
```

### Discard Local Changes

```bash
# Specific file
git checkout -- filename

# All files
git reset --hard HEAD
```

### View Commit History

```bash
# Simple log
git log --oneline

# Detailed log
git log --graph --decorate --all

# Search commits
git log --grep="feature"
```

### Check What Changed

```bash
# Unstaged changes
git diff

# Staged changes
git diff --cached

# Changes in specific file
git diff filename
```

## Resources

- [Git Documentation](https://git-scm.com/doc)
- [GitHub Guides](https://guides.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Git Ignore Patterns](https://git-scm.com/docs/gitignore)

## Quick Reference

```bash
# Status
git status

# Add files
git add .
git add filename

# Commit
git commit -m "message"

# Push
git push origin branch-name

# Pull
git pull origin branch-name

# Create branch
git checkout -b branch-name

# Switch branch
git checkout branch-name

# Merge
git merge branch-name

# View remotes
git remote -v

# View branches
git branch -a
```
