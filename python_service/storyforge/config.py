"""Configuration and environment for StoryForge AI."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from python_service)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

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
