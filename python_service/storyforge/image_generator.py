"""
Image Generator: Scene description → image file.
Supports placeholder (solid color + text), Hugging Face (Stable Diffusion), and optional OpenAI/Replicate.
Accepts optional character descriptions, visual instruction prompt, and movable (lifelike/dynamic) hint.
"""
import io
from pathlib import Path
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont
from .config import IMAGE_BACKEND, OUTPUT_DIR, PROJECT_ROOT

# Shown once when using placeholder so user knows why they don't see real images
_placeholder_warned = False

# CLIP (Stable Diffusion text encoder) has a 77-token limit. ~55 words keeps us safe.
MAX_PROMPT_WORDS = 55


def _truncate_prompt_for_clip(prompt: str, max_words: int = MAX_PROMPT_WORDS) -> str:
    """Truncate prompt so CLIP (77 tokens) doesn't truncate or error."""
    words = prompt.strip().split()
    if len(words) <= max_words:
        return prompt.strip()
    return " ".join(words[:max_words])


def build_image_prompt(
    description: str,
    character_descriptions: Optional[List[str]] = None,
    visual_instruction: Optional[str] = None,
    movable: bool = True,
    character_visible: bool = True,
) -> str:
    """
    Build the full prompt for image generation so the scene is understood correctly.
    Kept under CLIP 77-token limit so Stable Diffusion doesn't truncate or error.
    """
    parts = []
    if visual_instruction and visual_instruction.strip():
        parts.append(visual_instruction.strip())
    parts.append(description.strip())
    if character_descriptions:
        char_text = " ".join(character_descriptions)
        if char_text:
            parts.append(char_text)
    if character_visible:
        parts.append("character visible in frame")
    if movable:
        parts.append("cinematic, detailed")
    combined = ", ".join(p for p in parts if p)
    return _truncate_prompt_for_clip(combined)


def generate_character_image(
    name: str,
    description: str,
    output_dir: Path | None = None,
    width: int = 1024,
    height: int = 576,
) -> Path:
    """
    Generate a standalone image of a character (e.g. a girl) from the scene.
    Creates a portrait-style image so you get a clear character reference.
    """
    output_dir = output_dir or OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in name).strip() or "character"
    out_path = output_dir / f"character_{safe_name}.png"

    prompt = f"Portrait or full body image of {description}, cinematic lighting, high quality, detailed, 16:9 aspect ratio"
    if IMAGE_BACKEND == "huggingface":
        try:
            return _generate_huggingface(prompt, 0, out_path, width, height)
        except Exception as e:
            print(f"[Image] Character image failed ({e}), using placeholder.")
            return _generate_placeholder(f"{name}: {description}", 0, out_path, width, height)
    if IMAGE_BACKEND == "openai":
        try:
            return _generate_openai(prompt, 0, out_path, width, height)
        except Exception as e:
            print(f"[Image] Character image failed ({e}), using placeholder.")
            return _generate_placeholder(f"{name}: {description}", 0, out_path, width, height)
    if IMAGE_BACKEND == "replicate":
        try:
            return _generate_replicate(prompt, 0, out_path, width, height)
        except Exception as e:
            print(f"[Image] Character image failed ({e}), using placeholder.")
            return _generate_placeholder(f"{name}: {description}", 0, out_path, width, height)
    return _generate_placeholder(f"{name}: {description}", 0, out_path, width, height)


def generate_scene_image(
    description: str,
    scene_number: int,
    output_dir: Path | None = None,
    width: int = 1024,
    height: int = 576,
    character_descriptions: Optional[List[str]] = None,
    visual_instruction: Optional[str] = None,
    movable: bool = True,
) -> Path:
    """
    Generate an image for a scene. Returns path to saved image.
    character_descriptions: optional list of "Name: how they look" for consistent characters.
    visual_instruction: optional prompt (e.g. "cinematic, soft lighting, young girl in focus").
    movable: if True, add lifelike/dynamic hint so scene feels alive.
    """
    output_dir = output_dir or OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"scene_{scene_number:03d}.png"

    prompt = build_image_prompt(description, character_descriptions, visual_instruction, movable)

    if IMAGE_BACKEND == "huggingface":
        try:
            return _generate_huggingface(prompt, scene_number, out_path, width, height)
        except Exception as e:
            print(f"[Image] Hugging Face failed ({e}), using placeholder.")
            return _generate_placeholder(description, scene_number, out_path, width, height)

    if IMAGE_BACKEND == "openai":
        try:
            return _generate_openai(prompt, scene_number, out_path, width, height)
        except Exception as e:
            print(f"[Image] OpenAI failed ({e}), using placeholder.")
            return _generate_placeholder(description, scene_number, out_path, width, height)

    if IMAGE_BACKEND == "replicate":
        try:
            return _generate_replicate(prompt, scene_number, out_path, width, height)
        except Exception as e:
            print(f"[Image] Replicate failed ({e}), using placeholder.")
            return _generate_placeholder(description, scene_number, out_path, width, height)

    global _placeholder_warned
    if not _placeholder_warned:
        _placeholder_warned = True
        print("      [Image] Using PLACEHOLDER (text only, no girl/scene drawn). For real images set IMAGE_BACKEND=huggingface or openai in .env")
    return _generate_placeholder(description, scene_number, out_path, width, height)


def _generate_placeholder(
    description: str, scene_number: int, out_path: Path, width: int, height: int
) -> Path:
    """Create a placeholder image (cinematic aspect ratio, scene number + short text)."""
    img = Image.new("RGB", (width, height), color=(30, 30, 45))
    draw = ImageDraw.Draw(img)
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    text_title = f"Scene {scene_number}"
    short_desc = (description[:80] + "...") if len(description) > 80 else description
    # Center text
    bbox = draw.textbbox((0, 0), text_title, font=font_large)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((width - tw) // 2, (height - th) // 2 - 40), text_title, fill=(220, 220, 230), font=font_large)
    bbox2 = draw.textbbox((0, 0), short_desc, font=font_small)
    tw2, th2 = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    draw.text(((width - tw2) // 2, (height - th2) // 2 + 20), short_desc, fill=(180, 180, 200), font=font_small)
    img.save(out_path)
    return out_path


def _generate_huggingface(
    prompt: str, scene_number: int, out_path: Path, width: int, height: int
) -> Path:
    """Generate image using Hugging Face Diffusers (Stable Diffusion)."""
    from diffusers import StableDiffusionPipeline
    import torch

    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        safety_checker=None,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    pipe = pipe.to("cuda" if torch.cuda.is_available() else "cpu")
    full_prompt = f"cinematic, high quality, 16:9, {prompt}"
    image = pipe(
        full_prompt,
        num_inference_steps=25,
        width=width,
        height=height,
    ).images[0]
    image.save(out_path)
    return out_path


def _generate_openai(
    prompt: str, scene_number: int, out_path: Path, width: int, height: int
) -> Path:
    """Generate image using OpenAI DALL-E (if available)."""
    from openai import OpenAI
    from .config import OPENAI_API_KEY

    client = OpenAI(api_key=OPENAI_API_KEY)
    full_prompt = f"Cinematic scene, 16:9 aspect: {prompt}"
    response = client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size="1792x1024" if width > 1024 else "1024x1024",
        quality="standard",
        n=1,
    )
    url = response.data[0].url
    import urllib.request
    with urllib.request.urlopen(url) as resp:
        img = Image.open(io.BytesIO(resp.read())).convert("RGB")
    img = img.resize((width, height), Image.Resampling.LANCZOS)
    img.save(out_path)
    return out_path


def _generate_replicate(
    prompt: str, scene_number: int, out_path: Path, width: int, height: int
) -> Path:
    """Generate image using Replicate API (e.g. SDXL)."""
    import replicate
    from .config import REPLICATE_API_TOKEN

    if not REPLICATE_API_TOKEN:
        raise ValueError("REPLICATE_API_TOKEN not set")
    output = replicate.run(
        "stability-ai/sdxl:39a7aef825843b6d1c2f0a2e8e9c8d7b6a5f4e3d2c1b0a9",
        input={"prompt": f"cinematic, 16:9, {prompt}", "image_dimensions": f"{width}x{height}"},
    )
    url = output if isinstance(output, str) else output[0]
    import urllib.request
    with urllib.request.urlopen(url) as resp:
        img = Image.open(io.BytesIO(resp.read())).convert("RGB")
    img.save(out_path)
    return out_path
