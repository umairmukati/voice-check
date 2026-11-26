# Run it

macOS or Linux: run these in a terminal. Windows: use WSL (below).

```
# Clone
git clone <repo-url> gn-voice-check && cd gn-voice-check

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reproduce all numbers:
# Download LibriSpeech (first time only), 
# Test the voice check,
# Write results/summary.md, results/results.json and the plot
bash run.sh
```

- uv fetches Python 3.11 and the exact package versions in `uv.lock`. Nothing is compiled.
- Data: LibriSpeech test-clean, from a public GitHub copy ([aligned-librispeech](https://github.com/MontrealCorpusTools/aligned-librispeech)), downloaded once.
- Seeds are fixed, so the numbers repeat exactly.

## Files

```
run.sh            one command
pyproject.toml    dependencies (uv.lock pins them)
voicecheck/
  data.py         download, split 40 speakers into dev 20 and test 20
  embed.py        setup voice and test clips, 1 to 10 s
  channels.py     loudspeaker replay and motion sensor, simulated
  evaluate.py     choose limits on dev, report on test
  speakers.csv    speaker sex, from LibriSpeech
results/          summary.md, results.json, plot
```
