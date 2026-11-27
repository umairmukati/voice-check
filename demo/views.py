"""HTML pieces of the page. Styling lives in style.css."""
import math

from voice import THR, passes

SCRIPT = ("Hey, read me my new messages, please. Then book a meeting with Sophie for Thursday at half past nine, "
          "and remind me to call the garage about the blue car. If anyone asks, I'm working from the office near "
          "the river until five. Should I pay the June invoice of two hundred and forty euros now, or wait? "
          "Check the weather in Zurich, and play some quiet jazz while I finish this. Who called me this "
          "morning? Turn the volume up a little and switch on noise cancelling before my flight to Oslo. Send a "
          "short reply to Mark: yes, I can join the review at three, but only for thirty minutes. Thanks, that's "
          "everything for now.")
ACTIONS = [("read", "Read a message"), ("act", "Send, book, change"), ("pay", "Pay")]
LO, HI = 0.4, 1.0  # voice-match range shown on the gauges

ICONS = {  # 24 px line icons, drawn with currentColor
    "read": '<path d="M4 5h16v11H8l-4 4z"/><path d="M8 9h8M8 12h5"/>',
    "act": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "pay": '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M3 10h18M7 15h4"/>',
    "phone": '<rect x="7" y="3" width="10" height="18" rx="2"/><path d="M11 18h2"/>',
    "check": '<path d="M5 12l4 4 10-10"/>',
    "wait": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
}

HEADSET = """<svg class="vc-headset" viewBox="0 0 160 150" fill="none" stroke-linecap="round">
  <path d="M30 88V72a50 50 0 0 1 100 0v16" stroke="#6b6d73" stroke-width="9"/>
  <path d="M30 72a50 50 0 0 1 100 0" stroke="#8d8f95" stroke-width="3"/>
  <rect x="12" y="78" width="34" height="52" rx="15" fill="#2b2c30" stroke="#55575d" stroke-width="3"/>
  <rect x="114" y="78" width="34" height="52" rx="15" fill="#2b2c30" stroke="#55575d" stroke-width="3"/>
  <rect x="20" y="88" width="18" height="32" rx="9" fill="#38393e"/>
  <rect x="122" y="88" width="18" height="32" rx="9" fill="#38393e"/>
  <path d="M29 128c0 14 14 18 34 18" stroke="#6b6d73" stroke-width="4"/>
  <circle class="vc-accent" cx="68" cy="146" r="5"/>
  <circle class="vc-accent" cx="131" cy="104" r="4"/>
</svg>"""

HERO = ('<div class="vc-hero"><div><div class="vc-eyebrow">Voice check for a headset agent</div>'
        '<h1>Whose voice is this?</h1>'
        '<p>The agent works only for its owner. Set up an owner, then see who gets in.</p>'
        '<div class="vc-facts"><div class="vc-fact"><b>30 s</b><span>to set up</span></div>'
        '<div class="vc-fact"><b>3 s</b><span>to read a message</span></div>'
        f'<div class="vc-fact"><b>1 h</b><span>until recordings are deleted</span></div></div></div>{HEADSET}</div>')

STEP_SETUP = ('<div class="vc-step-head"><span class="vc-step-num">1</span><h3>Set up the owner</h3></div>'
              '<div class="vc-muted">Record the script below for about 30 s. Setup runs when you stop.</div>')

SCRIPT_BOX = ('<div class="vc-muted">Read it the way you talk to your headset; the first 30 s of speech are used.</div>'
              f'<div class="vc-script">{SCRIPT}</div>')

STEP_CHECK = ('<div class="vc-step-head"><span class="vc-step-num">2</span><h3>Who is speaking?</h3></div>'
              '<div class="vc-muted">Record or upload a request. It is checked when you stop.</div>')

EXAMPLES_NOTE = '<div class="vc-muted">Example requests for the example owner, LibriSpeech speaker 7176:</div>'

FOOT = ('<p class="vc-foot">Thresholds come from tests on read-aloud audiobooks (LibriSpeech, CC BY 4.0); example '
        'voices are LibriSpeech speakers 7176 (owner), 5639 and 7021. A laptop mic, noise or another room lower '
        'the owner\'s score, so expect more "not sure" than in the tests. Not shown here: the motion check against '
        'recordings, and the phone.</p>')


def icon(name, size=22):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{ICONS[name]}</svg>')


def frac(s):
    return min(max((s - LO) / (HI - LO), 0.0), 1.0)


def chip(on, text):
    return f'<span class="vc-chip {"on" if on else ""}"><span class="vc-dot"></span>{text}</span>'


def note(text):
    return f'<div class="vc-panel vc-note">{text}</div>'


def gauge(s, need):
    """Ring gauge: accent arc for the voice match, a white tick for what reading a message needs."""
    r, c = 62, 2 * math.pi * 62
    a = 2 * math.pi * frac(need) - math.pi / 2
    x1, y1, x2, y2 = 80 + 54 * math.cos(a), 80 + 54 * math.sin(a), 80 + 70 * math.cos(a), 80 + 70 * math.sin(a)
    return (f'<svg class="vc-gauge" viewBox="0 0 160 160">'
            f'<circle class="vc-g-track" cx="80" cy="80" r="{r}"/>'
            f'<circle class="vc-g-arc" cx="80" cy="80" r="{r}" stroke-dasharray="{frac(s) * c:.1f} {c:.1f}" '
            f'transform="rotate(-90 80 80)"/>'
            f'<line class="vc-g-tick" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}"/>'
            f'<text x="80" y="82" text-anchor="middle" class="vc-g-num">{s:.2f}</text>'
            f'<text x="80" y="104" text-anchor="middle" class="vc-g-label">VOICE MATCH</text></svg>')


def action_row(action, name, d, s):
    if action == "pay":
        kind, mark, status = "info", "phone", "Phone tap, always"
    elif passes(action, d, s):
        kind, mark, status = "on", "check", "Allowed"
    else:
        kind, mark, status = "", "wait", "Not sure: listen longer, then phone tap"
    return (f'<div class="vc-row"><span class="vc-row-icon">{icon(action)}</span><span class="vc-row-name">{name}</span>'
            f'<span class="vc-status {kind}">{icon(mark, 18)}{status}</span></div>')


def length_bar(d, s):
    need = THR["read"][f"{d:g}"]
    return (f'<div class="vc-bar-wrap"><div class="vc-bar">'
            f'<div class="vc-bar-fill {"on" if s >= need else ""}" style="height:{100 * frac(s):.0f}%"></div>'
            f'<div class="vc-bar-tick" style="bottom:{100 * frac(need):.0f}%"></div></div>'
            f'<span class="vc-bar-val">{s:.2f}</span><span class="vc-bar-len">{d:g} s</span></div>')


def result_panel(scores):
    """{speech length: voice match} -> verdict with gauge and one row per action, then the score per length."""
    d, s = max(scores), scores[max(scores)]
    owner = passes("read", d, s)
    return (f'<div class="vc-panel vc-result">'
            f'<div class="vc-res-left">{gauge(s, THR["read"][f"{d:g}"])}'
            f'<span class="vc-caption">from {d:g} s of speech</span></div>'
            f'<div><div class="vc-eyebrow">Result</div>'
            f'<div class="vc-res-title {"on" if owner else ""}">'
            f'{"Recognised as the owner" if owner else "Not recognised as the owner"}</div>'
            f'<div class="vc-rows">{"".join(action_row(a, n, d, s) for a, n in ACTIONS)}</div></div></div>'
            f'<div class="vc-panel"><div class="vc-eyebrow">How sure, second by second</div>'
            f'<div class="vc-muted">Voice match after each length of speech. The white line marks what reading a '
            f'message needs.</div><div class="vc-bars">{"".join(length_bar(k, v) for k, v in scores.items())}</div></div>')
