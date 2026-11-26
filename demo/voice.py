"""The voice check: speaker model, thresholds from results.json, and scoring. No web code here."""
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", message="FNV hashing")  # harmless numba notice, raised on import
from resemblyzer import VoiceEncoder, preprocess_wav  # noqa: E402

HERE = Path(__file__).parent
SR = 16000
SETUP_S = 30  # seconds of setup speech used
MIN_SETUP_S = 3
RESULTS = next(p for p in (HERE / "results.json", HERE.parent / "results" / "results.json") if p.exists())
THR = json.loads(RESULTS.read_text())["thresholds"]  # action -> speech length (s) -> voice threshold
LENGTHS = sorted(float(d) for d in THR["read"])
ENC = VoiceEncoder("cpu", verbose=False)


def speech(path):
    """Audio file -> 16 kHz speech with silence removed."""
    return preprocess_wav(Path(path))


def enrol(path):
    """Setup recording -> (owner embedding or None if too short, seconds of speech used)."""
    x = speech(path)[: SETUP_S * SR]
    return (ENC.embed_utterance(x) if len(x) >= MIN_SETUP_S * SR else None), len(x) / SR


def score(path, owner):
    """Request -> ({speech length (s): voice match against the owner}, seconds of speech heard)."""
    x = speech(path)
    usable = [d for d in LENGTHS if len(x) >= d * SR]
    return {d: float(ENC.embed_utterance(x[: int(d * SR)]) @ owner) for d in usable}, len(x) / SR


def passes(action, d, s):
    """True if voice match s, from d seconds of speech, is enough for the action."""
    return s >= THR[action][f"{d:g}"]
