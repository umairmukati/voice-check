"""Simulated channels: loudspeaker replay, and the headset motion sensor.

No public data exists for the motion sensor, so it is simulated:
when the wearer talks, the headset vibrates with the voiced part of
their speech (80 to 400 Hz). Sound from a loudspeaker barely moves it.
"""
import numpy as np
from scipy import signal

SR = 16000 # Sampling Rate
_VOICED = signal.butter(4, [80, 400], btype="band", fs=SR, output="sos")
_SPEAKER = signal.butter(4, [300, 5000], btype="band", fs=SR, output="sos")


def _rms(x):
    return np.sqrt(np.mean(x ** 2) + 1e-12)


def replay(wav, rng, rt60=0.3, snr_db=30):
    """Owner's voice played from a small loudspeaker in a room.

    Args:
        wav: speech, 16 kHz.
    Returns:
        The replayed speech, same length and loudness as wav.
    """
    y = signal.sosfilt(_SPEAKER, wav)
    t = np.arange(int(rt60 * SR)) / SR
    rir = rng.standard_normal(t.size) * np.exp(-6.9 * t / rt60)
    rir[0] = 1.0
    y = signal.fftconvolve(y, rir)[: len(wav)]
    y += rng.standard_normal(len(y)) * _rms(y) * 10 ** (-snr_db / 20)
    return (y * _rms(wav) / _rms(y)).astype(np.float32)


def vibration(wav, wearer_talking, rng, snr_db=0.0, leak_db=-30.0):
    """Motion sensor signal while the mics hear wav.

    Args:
        wav: sound at the mics, 16 kHz.
        wearer_talking: True if the wearer speaks; False if the sound comes from outside.
    Returns:
        Sensor signal, same length as wav.
    """
    voiced = signal.sosfilt(_VOICED, wav)
    gain = 1.0 if wearer_talking else 10 ** (leak_db / 20)
    noise_level = _rms(voiced) * 10 ** (-snr_db / 20)
    noise = rng.standard_normal(len(wav)) * noise_level
    motion = np.cumsum(rng.standard_normal(len(wav))) * noise_level / np.sqrt(len(wav))
    return gain * voiced + noise + motion


def _envelope(x, frame=320):
    n = len(x) // frame
    e = (x[: n * frame].reshape(n, frame) ** 2).mean(axis=1)
    return np.log(e + 1e-10)


def motion_match(mic, vib):
    """How well the motion sensor follows the speech.

    Args:
        mic: sound at the mics, 16 kHz.
        vib: motion sensor signal, same length.
    Returns:
        Correlation of their voice-band energy, -1 to 1. High means the wearer spoke.
    """
    a = _envelope(signal.sosfilt(_VOICED, mic))
    b = _envelope(signal.sosfilt(_VOICED, vib))
    if len(a) < 3:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])
