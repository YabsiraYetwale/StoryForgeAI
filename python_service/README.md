# StoryForge AI — Phase 1

**Transform written stories into cinematic videos automatically.**

Phase 1 is a **local prototype** that runs the full pipeline on your machine:

```
Story → AI Scene breakdown → Images per scene → Voice narration → Final MP4
```

## Quick start

### 1. Create environment and install dependencies

```bash
cd storyFpgy
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

For **zero cost** (no GPU, no API keys), use the minimal dependencies (from project root or `python_service/`):

```bash
pip install -r python_service/requirements-minimal.txt
```

If you see `No module named 'edge_tts'`, install TTS explicitly:

```bash
pip install edge-tts
```

No `.env` or API keys needed; the app uses placeholder images and paragraph-based scene split by default.

### 2. Zero cost (no API keys)

The app runs **with no API keys and no cost** by default:

- **Scene planning:** Paragraph-based split (no LLM). Optional free upgrade: use a local LLM like [Ollama](https://ollama.com) and set `OPENAI_API_BASE=http://localhost:11434/v1` and `SCENE_MODEL=llama3.2` in `.env`.
- **Images:** Placeholder images (a “Scene N” title card). Each scene gets a **slow zoom (Ken Burns)** so the video has subtle motion. For **real generated images** (still free): install full deps (`pip install -r requirements.txt`), set `IMAGE_BACKEND=huggingface` in `.env`, and run again (GPU recommended for speed).
- **Narration:** edge-tts (free). **Video:** MoviePy + FFmpeg (free).

You don’t need to create a `.env` file unless you want to change these defaults.

### 3. Run the pipeline

**From story text:**

```bash
python run_storyforge.py "Once upon a time, in a small village, there lived a young girl who loved to tell stories. Every evening she would sit under the old tree and share tales with the children."
```

**From a file:**

```bash
python run_storyforge.py --file my_story.txt
```

**Options:**

- `--output`, `-o` — Output directory (default: `./output`)
- `--name`, `-n` — Output video filename (default: `storyforge_YYYY-MM-DD_HH-MM-SS.mp4` so each run is saved and not overwritten)
- `--voice`, `-v` — TTS voice, e.g. `en-US-JennyNeural`, `en-GB-SoniaNeural`
- `--images`, `-i` — Use images from a folder instead of generating. Put one image per scene, named in order (e.g. `1.png`, `2.png` or `scene_01.jpg`, `scene_02.jpg`). Sorted by name; extra scenes use the last image.

The final video is written to `output/storyforge_output.mp4` (or your chosen path).

## Pipeline overview

| Step | Module | Description |
|------|--------|-------------|
| 1 | **Scene planner** | LLM breaks the story into scenes (visual description + narration text per scene). Without `OPENAI_API_KEY`, uses paragraph-based fallback. |
| 2 | **Image generator** | One image per scene. Backends: `placeholder` (no key), `huggingface` (Stable Diffusion), `openai` (DALL·E), or `replicate`. |
| 3 | **Narration** | edge-tts turns each scene’s narration text into speech (no API key). |
| 4 | **Video composer** | MoviePy + FFmpeg assemble images and audio into a single MP4. |

## Project structure

```
storyFpgy/
├── storyforge/
│   ├── __init__.py
│   ├── config.py          # Env and settings
│   ├── models.py          # Scene, SceneBreakdown
│   ├── scene_planner.py   # Story → scenes (LLM)
│   ├── image_generator.py # Scene → image
│   ├── narration.py       # TTS (edge-tts)
│   ├── video_composer.py  # Images + audio → MP4
│   └── pipeline.py        # Full pipeline
├── run_storyforge.py      # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Requirements

- **Python 3.10+**
- **FFmpeg** on PATH (for MoviePy video export)
- Optional: **GPU** for faster image generation with `IMAGE_BACKEND=huggingface`
- Optional: **OPENAI_API_KEY** for AI scene breakdown and/or DALL·E images

## Phase 1 scope (0–3 months)

- [x] Local prototype
- [x] Story → Scene (AI or fallback)
- [x] Scene → Image (placeholder / Hugging Face / OpenAI)
- [x] Narration (TTS)
- [x] Simple movie export (MP4)

Next (Phase 2): better cinematic quality, web UI, user accounts, faster generation.
