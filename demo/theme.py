"""Colours and font for Gradio's own components (audio, buttons). Our own HTML is styled in style.css."""
import gradio as gr

ACCENT = "#FFC400"
_PAIRS = {  # name: colour, set for light and dark mode alike, so the page is always dark
    "body_background_fill": "#17181a", "body_text_color": "#ececee",
    "block_background_fill": "#232427", "block_border_color": "#313236",
    "block_label_background_fill": "#2b2c30", "block_label_text_color": "#c9cace",
    "background_fill_secondary": "#1b1c1f",
    "button_primary_background_fill": ACCENT, "button_primary_text_color": "#111111",
    "button_secondary_background_fill": "#2b2c30", "button_secondary_text_color": "#ececee",
    "button_secondary_border_color": "#3a3b40",
}

THEME = gr.themes.Base(
    primary_hue=gr.themes.colors.yellow, neutral_hue=gr.themes.colors.zinc,
    font=[gr.themes.GoogleFont("Manrope"), "system-ui", "sans-serif"],
).set(
    **_PAIRS, **{f"{k}_dark": v for k, v in _PAIRS.items()},
    block_radius="16px", button_large_radius="999px", button_small_radius="999px",
)
FORCE_DARK = "() => document.body.classList.add('dark')"
