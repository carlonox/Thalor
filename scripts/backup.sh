#!/bin/bash
# =============================================================================
# Automated Backup Script
# =============================================================================
# Creates a git commit with current state and pushes to remote.
#
# Usage:
#   ./backup.sh [commit_message]
#
# Example:
#   ./backup.sh "Daily backup - 2026-08-08"
# =============================================================================

set -e

COMMIT_MSG=${1:-"Automated backup - $(date '+%Y-%m-%d %H:%M:%S')"}

echo "[backup] Creating backup..."

# Ensure .gitignore exists
if [ ! -f .gitignore ]; then
    cat > .gitignore <<EOF
data/
data-ops/
shared/
vault/
*.db
*.lock
__pycache__/
.env
.env.*
!.env.example
EOF
fi

# Ensure .gitattributes exists
if [ ! -f .gitattributes ]; then
    cat > .gitattributes <<EOF
* text=auto
*.sh text eol=lf
*.py text eol=lf
*.yaml text eol=lf
*.db binary
EOF
fi

# Stage all changes
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "[backup] No changes to commit"
else
    # Commit
    git commit -m "$COMMIT_MSG"
    echo "[backup] Committed: $COMMIT_MSG"
    
    # Push if upstream exists
    if git rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
        AHEAD=$(git rev-list --count '@{u}..HEAD' 2>/dev/null || echo "0")
        if [ "$AHEAD" -gt 0 ]; then
            git push
            echo "[backup] Pushed to remote"
        fi
    fi
fi

echo "[backup] Backup complete"
