"""Configuration and environment for StoryForge AI."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env: try project root first, then python_service (so python_service/.env works)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_SERVICE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv(_SERVICE_DIR / ".env")  # override with python_service/.env if present

# Paths: project root is repo root so output/ and .env stay there
PROJECT_ROOT = _PROJECT_ROOT
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Scene planning (LLM)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", None)
SCENE_MODEL = os.getenv("SCENE_MODEL", "gpt-4o-mini")

# Image generation
IMAGE_BACKEND = os.getenv("IMAGE_BACKEND", "placeholder")  # placeholder | huggingface | openai | replicate
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "")

# Video
DEFAULT_FPS = 24
DEFAULT_SCENE_DURATION_SEC = 5.0
NARRATION_EXTRA_PAD_SEC = 0.5
# Optional: turn each scene image into short video with real motion (Stable Video Diffusion). Heavy on RAM/VRAM.
USE_SCENE_VIDEO = os.getenv("USE_SCENE_VIDEO", "").lower() in ("1", "true", "yes")
