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


def owner_source(path, mine):
    """Track whose voice is set up: the example owner, or the user's own recording (kept to switch back to).

    Returns: example requests (shown only for the example owner), the user's recording, and which switch button shows.
    """
    if not path:
        return gr.skip(), gr.skip(), gr.skip(), gr.skip()
    example = Path(path).name == EXAMPLE_OWNER
    if not example:
        mine = path
    return (gr.Column(visible=example), mine, gr.Button(visible=not example),
            gr.Button(visible=mine is not None and path != mine))


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


with gr.Blocks(title="Whose voice is this?") as demo:
    owner = gr.State(None)
    my_setup = gr.State(None)  # the user's own setup recording, to switch back to after the example
    gr.HTML(views.HERO)
    with gr.Row(equal_height=False):
        with gr.Column():
            gr.HTML(views.STEP_SETUP)
            setup_audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Owner's voice",
                                   editable=False)
            with gr.Row():
                owner_status = gr.HTML(views.chip(False, "No owner set up"))
                setup_file = gr.UploadButton("Upload any audio file", size="sm", scale=0)
                example_owner = gr.Button("Use example owner", size="sm", scale=0)
                my_owner = gr.Button("Back to my recording", size="sm", scale=0, visible=False)
        with gr.Column():
            gr.HTML(views.STEP_CHECK)
            check_audio = gr.Audio(sources=["microphone", "upload"], type="filepath", label="Request", editable=False)
            check_file = gr.UploadButton("Upload any audio file", size="sm")
            with gr.Column(visible=False) as tries_box:
                gr.HTML(views.EXAMPLES_NOTE)
                with gr.Row():
                    tries = [(gr.Button(label, size="sm"), f) for label, f in TRIES]
    result = gr.HTML(views.note("Record or upload a request to see the result."))
    gr.HTML(views.FOOT)

    # Run as soon as the audio is ready. Several events can fire for one recording, some before the audio has
    # arrived; the handlers skip those. Only the clear button resets.
    setup_ready = [setup_audio.change, setup_audio.stop_recording, setup_audio.upload]
    gr.on(setup_ready, set_up, setup_audio, [owner, owner_status]).then(  # re-check any request for the new owner
        check, [check_audio, owner], result)
    gr.on(setup_ready, owner_source, [setup_audio, my_setup], [tries_box, my_setup, example_owner, my_owner])
    setup_audio.clear(lambda: (None, views.chip(False, "No owner set up"), gr.Column(visible=False)), None,
                      [owner, owner_status, tries_box])
    gr.on([check_audio.change, check_audio.stop_recording, check_audio.upload], check, [check_audio, owner], result)
    check_audio.clear(lambda: views.note("Record or upload a request to see the result."), None, result)
    setup_file.upload(any_file, setup_file, setup_audio)
    check_file.upload(any_file, check_file, check_audio)
    example_owner.click(lambda: str(EXAMPLES / EXAMPLE_OWNER), None, setup_audio)
    my_owner.click(lambda mine: mine, my_setup, setup_audio)
    for btn, f in tries:
        btn.click(lambda f=f: str(EXAMPLES / f), None, check_audio)

if __name__ == "__main__":
    demo.launch(theme=THEME, css=(HERE / "style.css").read_text(), js=FORCE_DARK, share=os.getenv("SHARE") == "1")
