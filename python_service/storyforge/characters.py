"""
Character handling: load from file or analyze from story for consistent visual generation.
"""
import json
import re
from pathlib import Path
from .models import CharacterDescription
from .config import OPENAI_API_KEY, OPENAI_API_BASE, SCENE_MODEL

EXTRACT_SYSTEM = """You are extracting character descriptions for a short film. Given a story, list each named or implied character with a short visual description for AI image generation (age, appearance, clothing, etc.). Output JSON only: {"characters": [{"name": "Name", "description": "visual description"}]}. Use 1-2 short sentences per description. If no clear characters, describe the main subject (e.g. "A person") with one entry."""


def load_characters_from_file(path: Path) -> list[CharacterDescription]:
    """Load character descriptions from a JSON or text file."""
    path = Path(path)
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if not text:
        return []

    # JSON: {"characters": [{"name": "...", "description": "..."}]} or [{"name": "...", "description": "..."}]
    if path.suffix.lower() == ".json":
        try:
            data = json.loads(text)
            if isinstance(data, list):
                return [CharacterDescription(**c) for c in data]
            if isinstance(data, dict) and "characters" in data:
                return [CharacterDescription(**c) for c in data["characters"]]
            if isinstance(data, dict) and "name" in data and "description" in data:
                return [CharacterDescription(**data)]
        except (json.JSONDecodeError, TypeError):
            pass

    # Plain text: "Name: description" per line (skip comments and empty lines)
    out = []
    for line in text.splitlines():
        line = line.strip().split("#")[0].strip()
        if ":" in line and not line.startswith("#"):
            name, _, desc = line.partition(":")
            name, desc = name.strip(), desc.strip()
            if name and desc:
                out.append(CharacterDescription(name=name, description=desc))
    return out


def analyze_characters_from_story(story: str) -> list[CharacterDescription]:
    """Use LLM to extract character names and visual descriptions from the story."""
    if not OPENAI_API_KEY and not OPENAI_API_BASE:
        return []
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY or "not-needed", base_url=OPENAI_API_BASE)
    response = client.chat.completions.create(
        model=SCENE_MODEL,
        messages=[
            {"role": "system", "content": EXTRACT_SYSTEM},
            {"role": "user", "content": f"Story:\n{story[:4000]}"},
        ],
        temperature=0.3,
    )
    text = response.choices[0].message.content.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [CharacterDescription(**c) for c in data]
        if isinstance(data, dict) and "characters" in data:
            return [CharacterDescription(**c) for c in data["characters"]]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return []
