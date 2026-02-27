"""
StoryForge AI - Simple web UI for free deployment (Hugging Face Spaces, or local).
Run: pip install gradio && python app_gradio.py
Then open the URL (e.g. http://127.0.0.1:7860). On Spaces, the app runs in the cloud.
"""
import importlib
import os
import sys
import tempfile
from pathlib import Path

# Default for free tier: placeholder (low RAM, no timeout). User can choose Hugging Face in the UI.
if "IMAGE_BACKEND" not in os.environ:
    os.environ["IMAGE_BACKEND"] = "placeholder"

_SERVICE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SERVICE_DIR))

try:
    import gradio as gr
except ImportError:
    print("Install Gradio: pip install gradio")
    sys.exit(1)

import storyforge.config
from storyforge.pipeline import run_pipeline


def run_storyforge_ui(story_text: str, voice: str, image_backend: str) -> tuple[str | None, str]:
    if not (story_text or "").strip():
        return None, "Enter a story."
    # Apply user choice: Hugging Face = real images (needs torch/diffusers, GPU or slow CPU)
    backend = "huggingface" if "hugging face" in (image_backend or "").lower() else "placeholder"
    os.environ["IMAGE_BACKEND"] = backend
    importlib.reload(storyforge.config)
    out_dir = Path(tempfile.mkdtemp(prefix="storyforge_"))
    try:
        out_path, breakdown = run_pipeline(
            story=story_text.strip(),
            output_dir=out_dir,
            output_filename="video.mp4",
            voice=voice or "en-US-JennyNeural",
            use_scene_video=False,
        )
        if out_path and out_path.exists():
            return str(out_path), f"Done: {len(breakdown.scenes)} scene(s)."
        return None, "Video generation failed."
    except Exception as e:
        return None, f"Error: {e}"


def main():
    with gr.Blocks(title="StoryForge AI", theme=gr.themes.Soft()) as app:
        gr.Markdown("# StoryForge AI – Turn a story into a video")
        story = gr.Textbox(
            label="Story",
            placeholder="Paste your story here...",
            lines=8,
        )
        image_backend = gr.Radio(
            label="Images",
            choices=[
                "Placeholder (fast, works on free CPU)",
                "Hugging Face (real images – needs GPU or ~10 min per image on CPU)",
            ],
            value="Placeholder (fast, works on free CPU)",
            info="Placeholder = text cards, no GPU. Hugging Face = Stable Diffusion, real scenes.",
        )
        voice = gr.Dropdown(
            label="Voice",
            choices=["en-US-JennyNeural", "en-GB-SoniaNeural", "en-US-GuyNeural"],
            value="en-US-JennyNeural",
        )
        btn = gr.Button("Generate video")
        video = gr.Video(label="Output video")
        status = gr.Markdown("")
        btn.click(
            fn=run_storyforge_ui,
            inputs=[story, voice, image_backend],
            outputs=[video, status],
        )
    app.launch(server_name="0.0.0.0" if os.getenv("SPACE_ID") else None)


if __name__ == "__main__":
    main()
