"""Choose limits and speech length on the dev speakers, measure them on the unseen test speakers.
"""
import json
from collections import Counter
from pathlib import Path

import matplotlib
import numpy as np
from scipy.stats import beta

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CACHE = Path("cache")
OUT = Path("results")

# What "safe" means per action: strangers let in at most `far`, owner shut out at most `frr`.
TIERS = {
    "read": {"far": 1e-2, "frr": 0.05},
    "act": {"far": 1e-3, "frr": 0.05},
    "pay": {"far": 1e-4, "frr": 0.05},
}
LOOKALIKES = 5   # attacker: the 5 closest same-sex voices per owner
MOTION_FRR = 0.01  # motion check may reject the real wearer 1% of the time (set on dev)
POOL = {"requests": 3, "each": 2.0, "versus": 5.0}  # own idea: three 2 s requests vs one 5 s


# ---------- Load ----------

def load(name):
    """Scores and trial masks for one half of the speakers.

    Args:
        name: "dev" or "test".
    Returns:
        Dict of arrays. Added to the cached ones:
            voice_match: cosine of clip and owner setup embeddings, clip x length x owner.
            voice_match_replay: same for the owner's replayed voice, against that owner only, clip x length.
            motion_match: mic vs motion sensor correlation, minus the owner's setup value, clip x length.
            motion_match_replay: same for replay, clip x length x leak.
            own, colleague, lookalike: trial masks, clip x owner.
    """
    p = dict(np.load(CACHE / f"{name}.npz"))
    pos = {s: i for i, s in enumerate(p["enrol_ids"])}
    p["spk"] = np.array([pos[s] for s in p["ids"]])  # owner index of each clip
    p["look"] = lookalikes(p["enrol"], p["enrol_sex"])
    p["voice_match"] = p["clean"] @ p["enrol"].T
    p["voice_match_replay"] = np.einsum("ndk,nk->nd", p["replay"], p["enrol"][p["spk"]])
    # Motion check per person: each score is judged against the owner's own score at setup.
    off = p["motion_match_setup"][p["spk"]]
    p["motion_match"] = p["motion_match"] - off
    p["motion_match_replay"] = p["motion_match_replay"] - off[:, :, None]
    p.update(trials(p["spk"], p["sex"], p))
    return p


def lookalikes(enrol, sex):
    """owner x speaker: True for the closest same-sex voices."""
    sim = enrol @ enrol.T
    look = np.zeros(sim.shape, bool)
    for t in range(len(enrol)):
        near = [j for j in np.argsort(-sim[t]) if j != t and sex[j] == sex[t]]
        look[t, near[:LOOKALIKES]] = True
    return look


def trials(spk, sex, p):
    """Masks (clip x owner) for the three kinds of trial: owner, same-sex colleague, lookalike."""
    own = np.zeros((len(spk), len(p["enrol_ids"])), bool)
    own[np.arange(len(spk)), spk] = True
    return {"own": own,
            "colleague": (sex[:, None] == p["enrol_sex"][None, :]) & ~own,
            "lookalike": p["look"][:, spk].T}


def pooled(p):
    """Own idea: average the embeddings of short requests from one wearing, then score."""
    k, i = POOL["requests"], index(p, POOL["each"])
    vecs, spk = [], []
    for t in range(len(p["enrol_ids"])):
        clips = np.where(p["spk"] == t)[0]
        for g in range(len(clips) // k):
            v = p["clean"][clips[g * k:(g + 1) * k], i].mean(axis=0)
            vecs.append(v / np.linalg.norm(v))
            spk.append(t)
    spk = np.array(spk)
    return {"voice_match": (np.array(vecs) @ p["enrol"].T)[:, None, :], **trials(spk, p["enrol_sex"][spk], p)}


def index(p, dur):
    return int(np.where(p["durs"] == dur)[0][0])


# ---------- Checks and statistics ----------

def voice_threshold(p, i, far):
    """Lowest voice score that lets in at most `far` of colleagues and of lookalikes."""
    s = p["voice_match"][:, i, :]
    q = lambda m: np.quantile(s[m], 1 - far, method="higher")  # noqa: E731
    return max(q(p["colleague"]), q(p["lookalike"]))


def shut_out(p, i, thr, motion_thr):
    """Per owner clip: True if the voice check or the motion check fails."""
    return (p["voice_match"][:, i, :][p["own"]] < thr) | (p["motion_match"][:, i] < motion_thr)


def ci(k, n):
    """Two-sided 95% interval on a rate (Clopper-Pearson)."""
    return [beta.ppf(0.025, k, n - k + 1) if k > 0 else 0.0, beta.ppf(0.975, k + 1, n - k) if k < n else 1.0]


def upper(k, n):
    """One-sided 95% upper bound on a rate after k errors in n trials."""
    return beta.ppf(0.95, k + 1, n - k) if k < n else 1.0


# ---------- Measure on test ----------

def measure(p, i, thr, motion_thr):
    """Every rate the report uses, at one speech length and one voice threshold."""
    s = p["voice_match"][:, i, :]
    shut = shut_out(p, i, thr, motion_thr)
    look = s[p["lookalike"]] >= thr
    replay_voice = p["voice_match_replay"][:, i] >= thr
    return {
        "owner_shut_out": shut.mean(), "owner_shut_out_ci": ci(shut.sum(), shut.size),
        "colleague_in": (s[p["colleague"]] >= thr).mean(),
        "lookalike_in": look.mean(), "lookalike_in_upper": upper(look.sum(), look.size),
        "replay_in_voice": replay_voice.mean(),
        "replay_in_both": {f"{leak:g} dB": (replay_voice & (p["motion_match_replay"][:, i, j] >= motion_thr)).mean()
                           for j, leak in enumerate(p["leaks"])},
    }


def choose(tier, dev, thr, motion_thr, measured):
    """Shortest speech whose owner lockout meets the limit on dev; shown at the longest if none."""
    lim, durs = TIERS[tier], list(dev["durs"])
    ok = [d for i, d in enumerate(durs) if shut_out(dev, i, thr[tier, d], motion_thr[i]).mean() <= lim["frr"]]
    shown = ok[0] if ok else durs[-1]
    m = measured[f"{shown:g}"]
    return {"speech": ok[0] if ok else None, "shown_at": shown,
            "met": m["owner_shut_out"] <= lim["frr"] and max(m["colleague_in"], m["lookalike_in"]) <= lim["far"],
            "proven": m["lookalike_in_upper"] <= lim["far"]}


def how_it_fails(p, dur, thr, motion_thr, frr):
    """At one length and threshold: strangers let in, and owners shut out more often than frr."""
    i = index(p, dur)
    clip, owner = np.nonzero((p["voice_match"][:, i, :] >= thr) & ~p["own"])
    pairs = Counter((str(p["ids"][c]), str(p["enrol_ids"][o]), bool(p["sex"][c] == p["enrol_sex"][o]))
                    for c, o in zip(clip, owner))
    shut = shut_out(p, i, thr, motion_thr)
    per_owner = {str(s): shut[p["spk"] == t].mean() for t, s in enumerate(p["enrol_ids"])}
    over = sorted(((s, v) for s, v in per_owner.items() if v > frr), key=lambda kv: -kv[1])
    rest = ~np.isin(p["ids"], [s for s, _ in over])
    return {
        "speech": dur,
        "strangers_in": [{"stranger": s, "owner": o, "same_sex": same, "times": c} for (s, o, same), c in pairs.most_common()],
        "owners_over_limit": over,
        "other_owners": {"count": len(per_owner) - len(over), "shut_out": shut[rest].mean()},
    }


def own_idea(dev, test, thr, measured):
    """Pooled short requests vs one longer request, at the act limit (voice check only)."""
    pd, pt = pooled(dev), pooled(test)
    t_pool = voice_threshold(pd, 0, TIERS["act"]["far"])
    s = pt["voice_match"][:, 0, :]
    i = index(test, POOL["versus"])
    single = measured["act"][f"{POOL['versus']:g}"]
    return {**POOL,
            "pooled": {"owner_shut_out": (s[pt["own"]] < t_pool).mean(),
                       "strangers_in": max((s[pt["colleague"]] >= t_pool).mean(), (s[pt["lookalike"]] >= t_pool).mean())},
            "single": {"owner_shut_out": (test["voice_match"][:, i, :][test["own"]] < thr["act", POOL["versus"]]).mean(),
                       "strangers_in": max(single["colleague_in"], single["lookalike_in"])}}


# ---------- Run ----------

def main():
    dev, test = load("dev"), load("test")
    durs = list(dev["durs"])

    # Calibrate on dev: motion threshold per length, voice threshold per action and length.
    motion_thr = np.quantile(dev["motion_match"], MOTION_FRR, axis=0)
    thr = {(t, d): voice_threshold(dev, i, lim["far"]) for t, lim in TIERS.items() for i, d in enumerate(durs)}

    # Measure on test.
    by_length = {t: {f"{d:g}": measure(test, i, thr[t, d], motion_thr[i]) for i, d in enumerate(durs)} for t in TIERS}
    answer = {t: choose(t, dev, thr, motion_thr, by_length[t]) for t in TIERS}
    d = answer["read"]["shown_at"]

    results = {
        "speakers": {"dev": len(dev["enrol_ids"]), "test": len(test["enrol_ids"])},
        "trials_per_length": {k: test[k].sum() for k in ("own", "colleague", "lookalike")},
        "limits": TIERS,
        "answer": answer,
        "by_length": by_length,
        "motion_check_fails": dict(zip((f"{x:g}" for x in durs), (test["motion_match"] < motion_thr).mean(axis=0))),
        "how_it_fails": how_it_fails(test, d, thr["read", d], motion_thr[index(test, d)], TIERS["read"]["frr"]),
        "own_idea": own_idea(dev, test, thr, by_length),
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(results, indent=1, default=lambda o: o.item()))

    results = json.loads((OUT / "results.json").read_text())  # report only from what was saved
    (OUT / "summary.md").write_text(summary(results))
    plot(results, OUT / "owner_lockout_by_speech.png")


# ---------- Report (from results.json only: measured values, no conclusions) ----------

def pct(x, n=1):
    return f"{100 * x:.{n}f}%"


def table(header, rows):
    return [f"| {' | '.join(header)} |", "|" + "---|" * len(header)] + [f"| {' | '.join(r)} |" for r in rows]


def summary(r):
    sp, n, lim, a, L, f, o = (r[k] for k in ("speakers", "trials_per_length", "limits", "answer", "by_length",
                                            "how_it_fails", "own_idea"))
    yn = lambda x: "yes" if x else "no"  # noqa: E731

    def answer_row(t):
        m = L[t][f"{a[t]['shown_at']:g}"]
        lo, hi = m["owner_shut_out_ci"]
        return [t, f"1 in {1 / lim[t]['far']:,.0f} / {pct(lim[t]['frr'])}",
                f"{a[t]['speech']:g} s" if a[t]["speech"] else "–", f"{a[t]['shown_at']:g} s",
                f"{pct(m['owner_shut_out'])} ({pct(lo)}–{pct(hi)})", pct(m["colleague_in"], 2),
                f"{pct(m['lookalike_in'], 2)} ({pct(m['lookalike_in_upper'], 2)})", yn(a[t]["met"]), yn(a[t]["proven"])]

    leaks = list(L["read"]["1"]["replay_in_both"])
    replay_rows = [[f"{d} s", pct(m["replay_in_voice"], 2), *(pct(m["replay_in_both"][k], 2) for k in leaks)]
                   for d, m in L["read"].items()]
    stranger_rows = [[x["stranger"], x["owner"], yn(x["same_sex"]), str(x["times"])] for x in f["strangers_in"]]
    owner_rows = [[s, pct(v)] for s, v in f["owners_over_limit"]]
    owner_rows.append([f"other {f['other_owners']['count']} owners", pct(f["other_owners"]["shut_out"])])
    req = f"{o['requests']} × {o['each']:g} s, pooled"

    lines = [
        "# Results", "",
        f"Test: {sp['test']} speakers. Limits and speech length chosen on {sp['dev']} other speakers. "
        f"Trials per speech length: {n['own']} owner, {n['colleague']} same-sex colleague, {n['lookalike']} lookalike.", "",
        "## Answer", "",
        *table(["Action", "Limits: strangers in / owner shut out", "Speech chosen on dev", "Measured at",
                "Owner shut out (95% CI)", "Colleague in", "Lookalike in (95% upper)", "Limits met", "Stranger limit proven"],
               [answer_row(t) for t in TIERS]),
        "", "## Owner shut out by speech length", "",
        *table(["Speech", *TIERS], [[f"{d} s", *(pct(L[t][d]["owner_shut_out"]) for t in TIERS)] for d in L["read"]]),
        "", "## Motion check: owner fails", "",
        *table(["Speech", *(f"{d} s" for d in r["motion_check_fails"])], [["Owner fails", *map(pct, r["motion_check_fails"].values())]]),
        "", "## Replay passes (simulated, read limit)", "",
        *table(["Speech", "Voice check", *(f"Voice + motion, leak {k}" for k in leaks)], replay_rows),
        "", f"## Strangers let in (read, {f['speech']:g} s)", "",
        *(table(["Stranger", "Owner", "Same sex", "Times"], stranger_rows) if stranger_rows else ["None."]),
        "", f"## Owners shut out over {pct(lim['read']['frr'], 0)} (read, {f['speech']:g} s)", "",
        *table(["Owner", "Shut out"], owner_rows),
        "", "## Own idea (act limit, voice check only)", "",
        *table(["Request", "Owner shut out", "Strangers in"],
               [[req, pct(o["pooled"]["owner_shut_out"]), pct(o["pooled"]["strangers_in"], 2)],
                [f"1 × {o['versus']:g} s", pct(o["single"]["owner_shut_out"]), pct(o["single"]["strangers_in"], 2)]]),
    ]
    return "\n".join(lines) + "\n"


def plot(r, path):
    plt.figure(figsize=(6, 4))
    for t, by_len in r["by_length"].items():
        plt.plot([float(d) for d in by_len], [100 * m["owner_shut_out"] for m in by_len.values()], marker="o",
                 label=f"{t} (strangers ≤ 1 in {1 / TIERS[t]['far']:,.0f})")
    plt.axhline(100 * TIERS["read"]["frr"], color="grey", ls="--", lw=1)
    plt.xlabel("speech in the check (s)")
    plt.ylabel("owner shut out (%)")
    plt.title("Owner shut out by speech length (test speakers)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=150)


if __name__ == "__main__":
    main()
