#!/usr/bin/env bash
# One command: download data, compute embeddings, write results/.
set -euo pipefail
cd "$(dirname "$0")"
command -v git >/dev/null || { echo "Needs git."; exit 1; }
command -v uv >/dev/null || { echo "Needs uv. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
run() { uv run -q --locked python -m "$@"; }

echo "[1/3] Data: LibriSpeech test-clean (about 500 MB, first time only)"
run voicecheck.data
echo "[2/3] Embeddings: 40 speakers, about 15 min on a laptop CPU"
run voicecheck.embed
echo "[3/3] Evaluation"
run voicecheck.evaluate
