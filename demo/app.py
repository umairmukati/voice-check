"""Voice check demo: set up an owner, then check who is speaking.

Run: uv run --group demo python demo/app.py      (add SHARE=1 for a temporary public link)
Files: voice.py (scoring), views.py (HTML), theme.py + style.css (look), app.py (layout and events).
"""
import os
from pathlib import Path

import gradio as gr

import views
import voice
from theme import FORCE_DARK, THEME

HERE = Path(__file__).parent
EXAMPLES = HERE / "examples"
EXAMPLE_OWNER = "owner_setup.wav"
TRIES = [("7176, another day", "owner_later.wav"), ("Colleague", "colleague.wav"), ("Lookalike", "lookalike.wav")]
HAS_EXAMPLES = all((EXAMPLES / f).exists() for f in [EXAMPLE_OWNER, *(f for _, f in TRIES)])  # built by make_examples


def log(event, path):
    print(f"[{event}] {Path(path).name if path else 'no audio yet'}", flush=True)


def set_up(path):
    """Owner's setup recording -> owner embedding and a status chip. Ignores events that carry no audio yet."""
    log("setup", path)
    if not path:
        return gr.skip(), gr.skip()
    owner, secs = voice.enrol(path)
    if owner is None:
        return None, views.chip(False, f"Only {secs:.1f} s of speech. Read the whole script.")
    return owner, views.chip(True, f"Owner ready, {secs:.0f} s of speech")


def example_requests(path):
    """Show the example requests only while the example owner is set up."""
    return gr.Column(visible=bool(path) and Path(path).name == EXAMPLE_OWNER)


def save_speaker(name, owner, saved):
    """Keep the current owner's voiceprint (not the recording) in this browser, under a name."""
    if owner is None:
        raise gr.Error("Set up an owner first, then save it.")
    name = (name or "").strip() or f"Speaker {len(saved) + 1}"
    saved = {**saved, name: [float(v) for v in owner]}
    return saved, gr.Dropdown(choices=list(saved), value=None), "", views.chip(True, f"Owner ready, saved as {name}")


def use_speaker(name, saved):
    """Pick a saved speaker as the owner. Clears the setup audio, which belonged to whoever was set up before."""
    if not name or name not in saved:
        return gr.skip(), gr.skip(), gr.skip(), gr.skip()
    return (voice.as_owner(saved[name]), views.chip(True, f"Owner: {name} (saved)"), None,
            gr.Column(visible=False))


def any_file(path):
    """Uploaded file of any type -> playable WAV for the audio box (which then runs setup or check)."""
    if not path:
        return gr.skip()
    try:
        return voice.to_wav(path)
    except Exception:
        raise gr.Error(f"Could not read {Path(path).name} as audio.")


def check(path, owner):
    """A request -> the result panel. Ignores events that carry no audio yet."""
    log("check", path)
    if not path:
        return gr.skip()
    if owner is None:
        return views.note("Set up the owner first.")
    scores, secs = voice.score(path, owner)
    if not scores:
        return views.note(f"Only {secs:.1f} s of speech. Say at least {voice.LENGTHS[0]:g} s.")
    return views.result_panel(scores)


# Gradio keeps recordings and uploads in a temp folder: check every 10 min, delete those older than KEEP_S.
with gr.Blocks(title="Whose voice is this?", delete_cache=(600, voice.KEEP_S)) as demo:
    owner = gr.State(None)
    saved = gr.BrowserState({}, storage_key="voice-check-speakers")  # name -> voiceprint, kept in this browser
    gr.HTML(views.HERO)
    with gr.Row(equal_height=False):
        with gr.Column():
            gr.HTML(views.STEP_SETUP)
            setup_audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Owner's voice",
                                   editable=False)
            with gr.Row(equal_height=True):
                setup_file = gr.UploadButton("Upload any audio file")
                example_owner = gr.Button("Use example owner", visible=HAS_EXAMPLES)
            owner_status = gr.HTML(views.chip(False, "No owner set up"))
            with gr.Row(equal_height=True):
                speaker_name = gr.Textbox(show_label=False, placeholder="Name this voice, e.g. Speaker 1",
                                          container=False, scale=3)
                save_btn = gr.Button("Save speaker", scale=1)
            saved_list = gr.Dropdown(choices=[], value=None, label="Saved speakers (kept in this browser)",
                                     interactive=True)
        with gr.Column():
            gr.HTML(views.STEP_CHECK)
            check_audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Request", editable=False)
            with gr.Row(equal_height=True):
                check_file = gr.UploadButton("Upload any audio file")
            with gr.Column(visible=False) as tries_box:
                gr.HTML(views.EXAMPLES_NOTE)
                with gr.Row(equal_height=True):
                    tries = [(gr.Button(label, size="sm"), f) for label, f in TRIES]
    result = gr.HTML(views.note("Record or upload a request to see the result."))
    gr.HTML(views.FOOT)

    # Run as soon as the audio is ready. Several events can fire for one recording, some before the audio has
    # arrived; the handlers skip those. Only the clear button resets.
    setup_ready = [setup_audio.change, setup_audio.stop_recording, setup_audio.upload]
    gr.on(setup_ready, set_up, setup_audio, [owner, owner_status]).then(  # re-check any request for the new owner
        check, [check_audio, owner], result)
    gr.on(setup_ready, example_requests, setup_audio, tries_box)
    setup_audio.clear(lambda: (None, views.chip(False, "No owner set up"), gr.Column(visible=False)), None,
                      [owner, owner_status, tries_box])
    gr.on([check_audio.change, check_audio.stop_recording, check_audio.upload], check, [check_audio, owner], result)
    check_audio.clear(lambda: views.note("Record or upload a request to see the result."), None, result)
    setup_file.upload(any_file, setup_file, setup_audio)
    check_file.upload(any_file, check_file, check_audio)
    example_owner.click(lambda: str(EXAMPLES / EXAMPLE_OWNER), None, setup_audio)
    for btn, f in tries:
        btn.click(lambda f=f: str(EXAMPLES / f), None, check_audio)

    # Saved speakers: survive a page reload, because they live in the browser's storage.
    demo.load(lambda s: gr.Dropdown(choices=list(s or {})), saved, saved_list)
    save_btn.click(save_speaker, [speaker_name, owner, saved], [saved, saved_list, speaker_name, owner_status])
    saved_list.input(use_speaker, [saved_list, saved], [owner, owner_status, setup_audio, tries_box]).then(
        check, [check_audio, owner], result)

if __name__ == "__main__":
    demo.launch(theme=THEME, css=(HERE / "style.css").read_text(), js=FORCE_DARK, share=os.getenv("SHARE") == "1")
