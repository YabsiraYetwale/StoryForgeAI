"""
Image Generator: Scene description → image file.
Supports placeholder (solid color + text), Hugging Face (Stable Diffusion), and optional OpenAI/Replicate.
"""
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .config import IMAGE_BACKEND, OUTPUT_DIR, PROJECT_ROOT


def generate_scene_image(
    description: str,
    scene_number: int,
    output_dir: Path | None = None,
    width: int = 1024,
    height: int = 576,
) -> Path:
    """
    Generate an image for a scene. Returns path to saved image.
    """
    output_dir = output_dir or OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"scene_{scene_number:03d}.png"

    if IMAGE_BACKEND == "huggingface":
        try:
            return _generate_huggingface(description, scene_number, out_path, width, height)
        except Exception as e:
            print(f"[Image] Hugging Face failed ({e}), using placeholder.")
            return _generate_placeholder(description, scene_number, out_path, width, height)

    if IMAGE_BACKEND == "openai":
        try:
            return _generate_openai(description, scene_number, out_path, width, height)
        except Exception as e:
            print(f"[Image] OpenAI failed ({e}), using placeholder.")
            return _generate_placeholder(description, scene_number, out_path, width, height)

    if IMAGE_BACKEND == "replicate":
        try:
            return _generate_replicate(description, scene_number, out_path, width, height)
        except Exception as e:
            print(f"[Image] Replicate failed ({e}), using placeholder.")
            return _generate_placeholder(description, scene_number, out_path, width, height)

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
    description: str, scene_number: int, out_path: Path, width: int, height: int
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
    prompt = f"cinematic, high quality, 16:9, {description}"
    image = pipe(
        prompt,
        num_inference_steps=25,
        width=width,
        height=height,
    ).images[0]
    image.save(out_path)
    return out_path


def _generate_openai(
    description: str, scene_number: int, out_path: Path, width: int, height: int
) -> Path:
    """Generate image using OpenAI DALL-E (if available)."""
    from openai import OpenAI
    from .config import OPENAI_API_KEY

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"Cinematic scene, 16:9 aspect: {description}"
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
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
    description: str, scene_number: int, out_path: Path, width: int, height: int
) -> Path:
    """Generate image using Replicate API (e.g. SDXL)."""
    import replicate
    from .config import REPLICATE_API_TOKEN

    if not REPLICATE_API_TOKEN:
        raise ValueError("REPLICATE_API_TOKEN not set")
    output = replicate.run(
        "stability-ai/sdxl:39a7aef825843b6d1c2f0a2e8e9c8d7b6a5f4e3d2c1b0a9",
        input={"prompt": f"cinematic, 16:9, {description}", "image_dimensions": f"{width}x{height}"},
    )
    url = output if isinstance(output, str) else output[0]
    import urllib.request
    with urllib.request.urlopen(url) as resp:
        img = Image.open(io.BytesIO(resp.read())).convert("RGB")
    img.save(out_path)
    return out_path
