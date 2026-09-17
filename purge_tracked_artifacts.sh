#!/usr/bin/env bash
# purge_tracked_artifacts.sh
#
# FIX (MN1, peer review packet): .gitignore was updated to exclude
# __pycache__/, *.pyc, and frontend/.next/**, but those paths were
# already committed in earlier commits, so .gitignore alone doesn't
# remove them from the working tree or from `git ls-files`. This script
# untracks them (keeping the files on disk, since .gitignore now covers
# them) and commits the cleanup as its own commit.
#
# Run this FROM THE ROOT OF YOUR LOCAL CLONE (not in this sandbox — this
# sandbox only has a tarball snapshot, not your real git history):
#
#   chmod +x purge_tracked_artifacts.sh
#   ./purge_tracked_artifacts.sh
#   git push
#
# If you want these gone from history entirely (not just the tip commit
# — e.g. because a reviewer or grader will inspect full history / clone
# size), use git-filter-repo instead; that rewrites history and requires
# a force-push, so coordinate with any collaborators first:
#
#   pip install git-filter-repo
#   git filter-repo --path backend/__pycache__ --path frontend/.next \
#       --invert-paths --force
#   git push --force

set -euo pipefail

echo "Untracking committed build/cache artifacts (keeping local copies)..."

git rm -r --cached --ignore-unmatch \
  backend/__pycache__ \
  backend/**/__pycache__ \
  backend/**/*.pyc \
  frontend/.next \
  frontend/node_modules \
  frontend-dev.err.log \
  frontend-dev.out.log

echo
echo "Verifying .gitignore actually covers these paths going forward..."
grep -q "__pycache__" backend/.gitignore || echo "__pycache__/" >> backend/.gitignore
grep -q "\.next" frontend/.gitignore || echo ".next/" >> frontend/.gitignore

git add backend/.gitignore frontend/.gitignore

git commit -m "chore: purge tracked build/cache artifacts (MN1, peer review packet)

__pycache__/*.pyc and frontend/.next/** were committed before .gitignore
excluded them. This untracks them (they remain on disk) and confirms
.gitignore covers both paths going forward. Repo language stats and
clone size should no longer be inflated by build output."

echo
echo "Done. Review with: git show --stat HEAD"
echo "Then: git push"
