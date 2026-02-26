"""
StoryForge AI Pipeline: Story → Scenes → Images → Narration → Movie.
"""
import re
from pathlib import Path
from .config import OUTPUT_DIR
from .models import SceneBreakdown
from .scene_planner import plan_scenes
from .image_generator import generate_scene_image
from .narration import generate_narration_audio
from .video_composer import compose_video

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def _get_images_from_folder(folder: Path) -> list[Path]:
    """Return image paths from folder, sorted by name (1, 2, 10 not 1, 10, 2)."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
    ]
    def sort_key(p: Path) -> tuple:
        # Extract numbers for natural sort (scene_1, scene_2, scene_10)
        parts = re.split(r"(\d+)", p.stem.lower())
        return tuple(int(x) if x.isdigit() else x for x in parts)
    files.sort(key=sort_key)
    return files


def run_pipeline(
    story: str,
    output_dir: Path | None = None,
    output_filename: str = "storyforge_output.mp4",
    voice: str = "en-US-JennyNeural",
    images_dir: Path | None = None,
) -> tuple[Path, SceneBreakdown]:
    """
    Run the full pipeline: story → scene breakdown → images → narration → MP4.
    If images_dir is set, use images from that folder (sorted by name) instead of generating.
    Returns (path_to_mp4, scene_breakdown).
    """
    output_dir = Path(output_dir or OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = output_dir / "run"
    run_dir.mkdir(exist_ok=True)

    print("[1/4] Breaking story into scenes...")
    breakdown = plan_scenes(story)
    print(f"      -> {len(breakdown.scenes)} scenes: {breakdown.title}")

    image_paths = []
    folder_images = _get_images_from_folder(images_dir) if images_dir else []

    if images_dir and not folder_images:
        print(f"      Warning: No images in {images_dir} (use .png, .jpg, etc.). Generating instead.")
        folder_images = []

    if folder_images:
        print(f"[2/4] Using {len(folder_images)} images from folder: {images_dir}")
        for scene in breakdown.scenes:
            idx = min(scene.scene_number - 1, len(folder_images) - 1)
            image_paths.append(folder_images[idx])
    else:
        print("[2/4] Generating images...")
        for scene in breakdown.scenes:
            img_path = generate_scene_image(
                scene.description,
                scene.scene_number,
                output_dir=run_dir,
            )
            image_paths.append(img_path)

    audio_paths = []
    print("[3/4] Generating narration (TTS)...")
    for scene in breakdown.scenes:
        audio_path = generate_narration_audio(
            scene.narration_text,
            scene.scene_number,
            output_dir=run_dir,
            voice=voice,
        )
        audio_paths.append(audio_path)

    print("[4/4] Composing video...")
    out_mp4 = output_dir / output_filename
    compose_video(
        scene_image_paths=image_paths,
        narration_audio_paths=audio_paths,
        output_path=out_mp4,
    )
    print(f"      -> Done: {out_mp4}")
    return out_mp4, breakdown
