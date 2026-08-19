#!/usr/bin/env bash
# Refresh the read-only mirror of our own suite into the internal git host.
#
# Runs nightly from CI. It mirrors OUR repository and nothing else: the source remote is
# pinned below and the script refuses to run against any other one, because a mirror job
# is exactly the kind of thing that quietly grows an extra remote.
set -euo pipefail

SOURCE_REMOTE="git@git.internal:sentinel/sentinel-bench.git"
MIRROR_REMOTE="git@git.internal:sentinel/sentinel-bench-mirror.git"
WORKDIR="${WORKDIR:-/var/tmp/sentinel-bench-mirror}"

if [ "${1:-}" != "" ] && [ "${1:-}" != "$SOURCE_REMOTE" ]; then
  echo "refusing: this script mirrors $SOURCE_REMOTE only" >&2
  exit 2
fi

if [ ! -d "$WORKDIR" ]; then
  git clone --mirror "$SOURCE_REMOTE" "$WORKDIR"
fi

cd "$WORKDIR"
git remote update --prune
git push --mirror "$MIRROR_REMOTE"
echo "mirror refreshed: $(git rev-parse --short HEAD 2>/dev/null || echo bare)"
