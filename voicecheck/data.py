"""Fetch LibriSpeech test-clean (40 speakers) and split it into two halves.
"""
import csv
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path("data/aligned-librispeech")
REPO = "https://github.com/MontrealCorpusTools/aligned-librispeech"
COMMIT = "5143690d1a6ebcd37b7f4d1b0f9fa8c83944aba5"
AUDIO = ROOT / "librispeech_test_clean"
PARTS = ["dev", "test"]  # dev: choose limits. test: report them.


def fetch():
    if AUDIO.exists():
        return
    subprocess.run(["git", "init", "-q", str(ROOT)], check=True)
    subprocess.run(["git", "-C", str(ROOT), "fetch", "-q", "--depth", "1", REPO, COMMIT], check=True)
    subprocess.run(["git", "-C", str(ROOT), "checkout", "-q", "FETCH_HEAD"], check=True)


def _sexes():
    with open(Path(__file__).with_name("speakers.csv")) as f:
        return {r["speaker"]: r["sex"] for r in csv.DictReader(f)}


def split():
    """10 women and 10 men in each half, alternating by speaker id."""
    halves = {p: [] for p in PARTS}
    by_sex = defaultdict(list)
    for spk, sex in _sexes().items():
        by_sex[sex].append(spk)
    for spks in by_sex.values():
        for i, spk in enumerate(sorted(spks, key=int)):
            halves[PARTS[i % 2]].append(spk)
    return halves


def speakers(part):
    """{speaker: {"sex": "M"/"F", "chapters": [[wav, ...], ...]}}"""
    sex = _sexes()
    out = {}
    for spk in sorted(split()[part], key=int):
        chapters = defaultdict(list)
        for wav in sorted((AUDIO / spk).glob("*.wav")):
            chapters[wav.name.split("-")[1]].append(wav)
        out[spk] = {"sex": sex[spk], "chapters": [chapters[c] for c in sorted(chapters)]}
    return out


if __name__ == "__main__":
    fetch()
