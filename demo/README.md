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

**Share:** `SHARE=1 uv run --group demo python demo/app.py` prints a temporary public link that works while the app runs. Open it on any device, phones included.
