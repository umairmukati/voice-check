"""Write the demo's example clips from the downloaded LibriSpeech test-clean (CC BY 4.0).

Owner 7176: 30 s setup from one chapter, and a later request from another chapter.
Strangers, both men like the owner: 5639 (colleague) and 7021 (one of the owner's closest voices).
"""
from pathlib import Path

import numpy as np
import soundfile as sf

from voicecheck.data import speakers

OUT = Path(__file__).parent / "examples"
SR = 16000


def chapter_audio(files, seconds):
    """Join consecutive files of one chapter until `seconds` of audio."""
    wavs = []
    for f in files:
        wavs.append(sf.read(f, dtype="float32")[0])
        if sum(map(len, wavs)) >= seconds * SR:
            break
    return np.concatenate(wavs)[: int(seconds * SR)]


def main():
    test = speakers("test")
    OUT.mkdir(exist_ok=True)
    clips = {
        "owner_setup.wav": chapter_audio(test["7176"]["chapters"][0], 30),
        "owner_later.wav": chapter_audio(test["7176"]["chapters"][1], 8),
        "colleague.wav": chapter_audio(test["5639"]["chapters"][0], 8),
        "lookalike.wav": chapter_audio(test["7021"]["chapters"][0], 8),
    }
    for name, x in clips.items():
        sf.write(OUT / name, x, SR)
        print(f"  {OUT / name}: {len(x) / SR:.0f} s")


if __name__ == "__main__":
    main()
