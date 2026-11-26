# Report

## Approach

One open speaker model (Resemblyzer), a 30 s setup per person, and a cosine score against the setup. A request passes if its voice score is high enough (voice check) and the motion sensor moves with the speech (motion check). Limits and speech length are chosen on 20 speakers and reported on 20 others (LibriSpeech test-clean).

Why Resemblyzer: open, small (17 MB) and fast on a laptop CPU (0.4 s for a 3 s request), so it could fit on a headset.

## Answer

No speech length meets a 5% owner lockout for any action, even 10 s. So I chose each length where more speech stops helping, and the check never refuses outright: when unsure, it listens longer, then asks for one tap on the phone.

| Action | Strangers let in | Owner shut out | Speech | Result on unseen speakers | Check |
|---|---|---|---|---|---|
| Read a message aloud | 1 in 100 | 5% | **3 s** | owner shut out 9.6%, lookalike in 0.26% | voice, then phone tap |
| Send, book, change | 1 in 1,000 | 5% | **5 s** | owner shut out 15.8%, no lookalike in | voice, then phone tap |
| Pay | 1 in 10,000 | 5% | – | 2,663 lookalike trials prove only "below 1 in 900" | phone tap always |

Past 3 s, more speech barely helps: read is 9.6% at 3 s and 8.5% at 10 s. The lockouts come from a few owners, not from short speech.

**Stranger:** both. A colleague is anyone else of the same sex. An attacker is one of the 5 voices closest to the owner, same sex. The limit must hold for both. Attackers get in about twice as often as colleagues (0.04% vs 0.02% at read, 10 s).

**Recorded voice:** played from a loudspeaker, the owner's voice passes the voice check in at most 0.2% of tries and never passes the motion check too, unless the loudspeaker sound reaches the motion sensor as strongly as the wearer's own voice (then 1 clip in 530).

![Owner shut out vs speech](../results/owner_lockout_by_speech.png)

## Why these limits

- **Read, 1 in 100.** A wrong read leaks one message to someone already holding the headset.
- **Act, 1 in 1,000.** A wrong email or booking can be undone, but others see it.
- **Pay, 1 in 10,000.** Money cannot be undone. FIDO certifies biometrics at this rate.
- **Owner shut out, 5%.** Above that, people stop using the feature.

## How it fails

- **Short speech.** At 1 s the owner is shut out 42% even at the read limit.
- **A few owners cause most lockouts.** At read, 10 s, 5 of 20 owners are over 5%; the other 15 are shut out 0.8%. The worst, 4446, is shut out 84%: the setup chapter sounds unlike the later ones.
- **Strangers who get in are the same sex.** At read, 10 s, one colleague got in (7021 into 7176).
- **The limits are stricter than needed.** Set on 20 dev speakers, they let in far fewer strangers on test than allowed (0.26% vs 1%), and the owner pays for it.
- **Motion check costs the owner 0.8 to 1.9%.** Its threshold is set per person, from the setup.

## The whole day

| Signal | Answers | Source |
|---|---|---|
| Voice check | Is this the owner's voice? | microphones, 30 s setup |
| Motion check | Is the person speaking the one wearing the headset? | motion sensor vs microphones |
| On-head | Has the headset left the owner since the last check? | wear sensor |
| Phone link | Is the owner's phone close, and can it confirm? | Bluetooth |

1. **Put on.** Trust is zero. The first request runs the voice and motion check with enough speech for its action.
2. **Worn.** Trust holds. Every request still runs the cheap motion check, so the owner does not prove who they are all day.
3. **Taken off.** Trust drops to zero at once.
4. **Someone else puts it on.** The motion check passes, the voice check fails, so nothing is read or done, and the owner's phone gets a notice.

**Recorded or cloned voices.** A recording or clone played from a speaker fails the motion check: the sensor does not move with outside sound, however good the clone. Someone wearing the headset and playing a clone into it fails too: their jaw does not move with it. A tampered headset is caught by the phone tap for acting and paying. A spoof detector could be one more signal, never the only one: detectors miss new kinds of clones.

**When it is not sure.** Three outcomes, not two. First listen a little longer; if still unsure, or for a payment, one tap on the phone; if refused, the agent says it cannot do that now, never which check failed. Reading still works while a payment waits, so one weak clip never locks the owner out.

## Own idea: evidence builds during a wearing

Pool the short requests made while the headset stays on. Three 2 s requests shut the owner out 18.0% at the act limit, worse than one 5 s request (14.5%, voice only). Pooling lets short requests add up, but it does not beat speaking longer.

## What I cut, and the limits

- **Voice clones.** Testing them needs a cloning tool and my own voice; the motion check does not depend on clone quality.
- **Real sensor data.** None is public, so the motion sensor and loudspeaker are simulated.
- **Real conditions.** 40 read-aloud speakers, clean audio; noise, accents and headset microphones will be worse.
- **More speakers.** Proving the pay limit needs about 30,000 attacker trials; this data has 2,663.
- **A model for short speech.** Resemblyzer was not trained for it; one that was would do better.

## What I would fix first

1. **Check the setup.** Ask for more speech when the setup does not match the owner's own later speech well (owner 4446).
2. **Real headset audio.** Record with a headset, in noise, with a real motion sensor.
3. **More speakers,** to prove the act and pay limits.

## Demo and tools

A small web app sets up your own voice and checks who is speaking: see the [README](../README.md#demo). Built with Python, Resemblyzer (GE2E), NumPy, SciPy, Matplotlib and Gradio. Full numbers: [results/summary.md](../results/summary.md).
