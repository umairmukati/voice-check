#!/usr/bin/env bash
# Publish the demo to a Hugging Face Space (created private if it does not exist).
# Usage: bash demo/deploy.sh <user>/<space>   (log in once first: uv run --group demo hf auth login)
set -euo pipefail
cd "$(dirname "$0")/.."
SPACE=${1:?usage: bash demo/deploy.sh <user>/<space>}

[ -f results/results.json ] || { echo "Run bash run.sh first."; exit 1; }
[ -d demo/examples ] || uv run -q --locked python -m demo.make_examples

stage=$(mktemp -d)
cp demo/app.py demo/voice.py demo/views.py demo/theme.py demo/style.css demo/requirements.txt demo/README.md \
   results/results.json "$stage"/
cp -R demo/examples "$stage"/examples
uv run -q --locked --group demo hf upload "$SPACE" "$stage" . --repo-type space --private
echo "Space: https://huggingface.co/spaces/$SPACE"
