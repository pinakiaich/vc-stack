# Git Sync Commands for GitHub

## Current Status
- **Branch:** `feature/v2-deal-workspace`
- **Status:** Changes committed, ready to push

## Commands to Run (in order)

### 1. Push to GitHub
```bash
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"
git push origin feature/v2-deal-workspace
```

You'll be prompted for your GitHub credentials (username/password or token).

### 2. If Push Fails (Authentication Issues)

If you get authentication errors, you have two options:

#### Option A: Use Personal Access Token (Recommended)
1. Generate a token: https://github.com/settings/tokens
2. Use token as password when prompted
3. Or configure credential helper:
```bash
git config --global credential.helper osxkeychain
```

#### Option B: Use SSH (Alternative)
If you prefer SSH instead of HTTPS:
```bash
# Check current remote
git remote -v

# If using HTTPS, switch to SSH
git remote set-url origin git@github.com:pinakiaich/vc-stack.git

# Then push
git push origin feature/v2-deal-workspace
```

### 3. Verify Push Success
```bash
git log --oneline -5
git status
```

You should see:
- "Your branch is up to date with 'origin/feature/v2-deal-workspace'"
- All commits visible in log

## What Was Committed

### New Files:
- `company_research_agent.py` - Company research agent with internet search
- `WORKFLOW_RESTRUCTURE_COMPLETE.md` - Documentation

### Modified Files:
- `streamlit_app.py` - Auto-create deals + research UI
- `backend/app/main.py` - Research findings API endpoints
- `requirements.txt` - Added duckduckgo-search dependency

## Next Steps After Push

1. **Update Pull Request** (if already open):
   - Go to GitHub PR page
   - New commits will automatically appear

2. **Or Create New Pull Request**:
   - Go to: https://github.com/pinakiaich/vc-stack
   - Click "Compare & pull request"
   - Base: `main`, Compare: `feature/v2-deal-workspace`

## Quick Copy-Paste Commands

```bash
# Navigate to project
cd "/Users/pinakiaich/Documents/Personal/Python Projects/vc-stack"

# Push to GitHub
git push origin feature/v2-deal-workspace
```

That's it! 🚀
