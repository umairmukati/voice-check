"""Embed each speaker's 30 s setup and test clips of several lengths."""
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore", message="FNV hashing")  # harmless numba notice, raised on import
from resemblyzer import VoiceEncoder, preprocess_wav  # noqa: E402

from . import channels
from .data import PARTS, speakers

SR = 16000 # Sampling Rate
DURS = [1.0, 2.0, 3.0, 5.0, 10.0]  # seconds of speech, silence removed
LEAKS = [-30.0, -10.0, 0.0]  # loudspeaker sound reaching the motion sensor (dB); -30 is assumed
ENROL_S = 30
N_TEST = 40  # test clips per speaker, at most
CACHE = Path("cache")


def segments(chapters, used, span):
    """Test clips, joined from consecutive utterances of one chapter.

    Args:
        chapters: the speaker's audio files, per chapter. The first is the setup chapter.
        used: files already used for the setup.
        span: clip length in samples.
    Yields:
        Speech of at least span samples. Other chapters first (another day), then the rest of the setup chapter.
    """
    order = [list(ch) for ch in chapters[1:]] + [[f for f in chapters[0] if f not in used]]
    for files in order:
        buf = []
        for f in files:
            buf.append(preprocess_wav(f))
            if sum(map(len, buf)) >= span:
                yield np.concatenate(buf)
                buf = []


def setup_motion_match(setup, d, rng):
    """The owner's typical motion match, from the setup.

    Args:
        setup: the 30 s setup speech.
        d: piece length (s), the same as the test clip.
    Returns:
        Median motion match over the pieces.
    """
    n = int(d * SR)
    return float(np.median([channels.motion_match(x, channels.vibration(x, True, rng))
                            for x in (setup[j * n:(j + 1) * n] for j in range(len(setup) // n))]))


def build(part, enc, rng):
    """Setup and test data for one half of the speakers.

    Args:
        part: "dev" or "test".
        enc: Resemblyzer voice encoder.
    Returns:
        Arrays, per test clip and speech length: voice embeddings (clean and replayed)
        and motion matches (owner and replay). Per speaker: setup embedding and setup motion match.
    """
    out ={k: [] for k in ["ids", "sex", "clean", "replay", "motion_match", "motion_match_replay"]}
    enrol_ids, enrol_sex, enrol, motion_match_setup = [], [], [], []
    span = int(max(DURS) * SR)
    spks, clips = speakers(part), 0
    for done, (spk, info) in enumerate(spks.items(), 1):
        chapters = info["chapters"]
        # Setup: 30 s of speech from the first chapter (one session).
        wavs, used = [], set()
        for f in chapters[0]:
            wavs.append(preprocess_wav(f))
            used.add(f)
            if sum(map(len, wavs)) >= ENROL_S * SR:
                break
        setup = np.concatenate(wavs)[: ENROL_S * SR]
        enrol.append(enc.embed_utterance(setup))
        # The owner's own motion match at setup: later scores are judged against it.
        motion_match_setup.append([setup_motion_match(setup, d, rng) for d in DURS])
        enrol_ids.append(spk)
        enrol_sex.append(info["sex"])
        n = 0
        for w in segments(chapters, used, span):
            start = rng.integers(0, len(w) - span + 1)
            seg = w[start:start + span]
            rows = {k: [] for k in ["clean", "replay", "motion_match", "motion_match_replay"]}
            for d in DURS:
                x = seg[: int(d * SR)]
                y = channels.replay(x, rng)
                rows["clean"].append(enc.embed_utterance(x))
                rows["replay"].append(enc.embed_utterance(y))
                rows["motion_match"].append(channels.motion_match(x, channels.vibration(x, True, rng)))
                rows["motion_match_replay"].append(
                    [channels.motion_match(y, channels.vibration(y, False, rng, leak_db=L)) for L in LEAKS])
            for k, v in rows.items():
                out[k].append(v)
            out["ids"].append(spk)
            out["sex"].append(info["sex"])
            n += 1
            if n == N_TEST:
                break
        clips += n
        print(f"\r  {part}: {done}/{len(spks)} speakers, {clips} test clips", end="", flush=True)
    print()
    out = {k: np.array(v) for k, v in out.items()}
    out.update(enrol=np.array(enrol), enrol_ids=np.array(enrol_ids), enrol_sex=np.array(enrol_sex),
               motion_match_setup=np.array(motion_match_setup), durs=np.array(DURS), leaks=np.array(LEAKS))
    return out


if __name__ == "__main__":
    CACHE.mkdir(exist_ok=True)
    enc = VoiceEncoder("cpu", verbose=False)
    for i, part in enumerate(PARTS):
        np.savez(CACHE / f"{part}.npz", **build(part, enc, np.random.default_rng(i)))
