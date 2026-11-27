# Whose voice is this?

A voice check for a headset AI agent: from a few seconds of speech, is this the owner or someone else?

**Write-up: [docs/report.md](docs/report.md)**: approach, answer, how it fails, the whole-day design.

## Run

In a macOS or Linux terminal. On Windows, run `wsl --install` in PowerShell once, then use the Ubuntu app.

```
# Clone
git clone https://github.com/umairmukati/voice-check && cd voice-check

# Install uv (once, if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reproduce all numbers, writes results/
bash run.sh
```

`run.sh` downloads LibriSpeech test-clean (about 500 MB, first time only), tests the voice check and writes `results/summary.md`, `results/results.json` and the plot. uv installs Python 3.11 and the exact versions in `uv.lock`; seeds are fixed, so the numbers repeat exactly.

## Demo

```
# Build the example clips (once, after run.sh)
uv run python -m demo.make_examples

# Start the app, then open http://127.0.0.1:7860
uv run --group demo python demo/app.py
```

Set up an owner from the microphone or a file, then check who is speaking. Add `SHARE=1` in front of the second command for a temporary public link, for example to open it on a phone.

## Files

```
run.sh          one command
voicecheck/     data.py (download, split), embed.py (setup and test clips),
                channels.py (simulated replay and motion sensor), evaluate.py (limits, results)
demo/           web app
results/        summary.md, results.json, plot
docs/report.md  the write-up
```

