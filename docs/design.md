# Whole-day design

The voice check answers one question. Three more signals keep the answer true through the day.

| Signal | Answers | Source |
|---|---|---|
| Voice check | Is this the owner's voice? | microphones, 30 s setup |
| Wearer check | Is the person speaking the one wearing the headset? | motion sensor vs microphones |
| On-head | Has the headset left the owner since the last check? | wear sensor |
| Phone link | Is the owner's phone close, and can it confirm? | Bluetooth |

## A day, step by step

1. **Put on.** Trust is zero. The first request runs the full check: enough speech for its action (see [report](report.md)), voice check and wearer check.
2. **Worn.** Trust holds while the headset stays on. Every later request still runs the wearer check (cheap, every time) and adds its speech to the evidence. So later requests need little or no extra speech: the owner does not prove who they are all day.
3. **Taken off** (lunch, desk). Trust drops to zero at once.
4. **Someone else puts it on.** They start at step 1. The wearer check passes (they are wearing it), the voice check fails, so nothing is read or done. The owner's phone gets a notice.

## Recorded or cloned voices

| Attack | Stopped by |
|---|---|
| Owner's voice played from a speaker or phone | Wearer check: the motion sensor does not move with sound from outside, however good the clone. Tested in simulation, see results. |
| Someone wears the headset and talks in their own voice | Voice check |
| Someone wears it and plays a clone into it | Wearer check: their jaw does not move with the clone |
| Tampered headset that fakes the sensor | Phone confirmation for acting and paying |

A spoof detector can be added later as one more signal, never the only one: detectors miss new kinds of clones.

## When it is not sure

Three outcomes, not two: accept, refuse, or one extra step.

1. Listen a little longer: the agent asks the owner to finish or repeat the request. Scores are kept every half second, and the check decides as soon as it is clear.
2. Still unsure, or a payment: one tap on the phone.
3. Refused: the agent says it cannot do that now, never which check failed, and the owner's phone shows the attempt.

Reading still works while a payment waits for the phone, so the owner is never fully locked out by one weak clip.

## Own idea: evidence builds during a wearing

Short requests are the hard case. But a headset that stayed on has heard its wearer many times since it was put on. Pooling those requests lets short requests add up to the evidence of a longer one, without asking the owner to speak longer. In tests, three 2 s requests were about as good as one 5 s request, not better (see [report](report.md)). A payment can rest on that, a fresh wearer check and the phone tap.
