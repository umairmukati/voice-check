---
title: Voice Check
colorFrom: yellow
colorTo: gray
sdk: gradio
sdk_version: 6.32.0
python_version: "3.11"
app_file: app.py
pinned: false
---

# Voice check demo

Set up an owner from about 30 s of speech, then check who is speaking.

**Run** (after `bash run.sh`):
```
uv run python -m demo.make_examples
uv run --group demo python demo/app.py      # http://127.0.0.1:7860
```

**Share:**
- Permanent: `uv run --group demo hf auth login`, then `bash demo/deploy.sh <user>/voice-check`, then make the Space public in its Settings.
- Temporary: `SHARE=1 uv run --group demo python demo/app.py` prints a public link that works while the app runs.
