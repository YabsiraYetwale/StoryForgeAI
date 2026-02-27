"""
StoryForge AI Pipeline: Story → Scenes → Images → Narration → Movie.
"""
import re
from pathlib import Path
from typing import List, Optional

from .config import OUTPUT_DIR, USE_SCENE_VIDEO
from .models import SceneBreakdown, CharacterDescription
from .scene_planner import plan_scenes
from .image_generator import generate_scene_image, generate_character_image
from .narration import generate_narration_audio
from .video_composer import compose_video
from .characters import load_characters_from_file, analyze_characters_from_story
from . import scene_video

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def _get_narration_files_from_folder(folder: Path) -> list[Path]:
    """Return narration_001.mp3, narration_002.mp3, ... sorted by number."""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    files = [
        f for f in folder.iterdir()
        if f.is_file() and f.suffix.lower() == ".mp3" and f.stem.lower().startswith("narration_")
    ]
    def sort_key(p: Path) -> tuple:
        parts = re.split(r"(\d+)", p.stem.lower())
        return tuple(int(x) if x.isdigit() else x for x in parts)
    files.sort(key=sort_key)
    return files


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
    characters_file: Path | None = None,
    analyze_characters: bool = False,
    visual_instruction: str | None = None,
    movable: bool = True,
    generate_character_images: bool = False,
    use_scene_video: bool | None = None,
    use_existing_run: bool = False,
    only_scene: int | None = None,
) -> tuple[Path, SceneBreakdown]:
    """
    Run the full pipeline: story → scene breakdown → images → narration → MP4.
    use_existing_run: if True, use existing scene images and narration in output_dir/run/ (skip generation, only compose).
    If images_dir is set, use images from that folder (sorted by name) instead of generating.
    characters_file: optional path to JSON/txt with character descriptions (Name: how they look).
    analyze_characters: if True and no file, extract character descriptions from story via LLM.
    visual_instruction: optional prompt for how scenes should look (e.g. "young girl in focus, soft light").
    movable: if True, add lifelike/dynamic hint to image prompts.
    generate_character_images: if True, create one image per character (e.g. girl) in output/run/characters/.
    use_scene_video: if True, turn each scene image into short video with real motion (SVD). Default from USE_SCENE_VIDEO env.
    Returns (path_to_mp4, scene_breakdown).
    """
    if use_scene_video is None:
        use_scene_video = USE_SCENE_VIDEO
    output_dir = Path(output_dir or OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    run_dir = output_dir / "run"
    run_dir.mkdir(exist_ok=True)

    # Use existing output/run content (scenes + narration) and only compose video
    if use_existing_run:
        existing_images = _get_images_from_folder(run_dir)
        existing_narrations = _get_narration_files_from_folder(run_dir)
        n = min(len(existing_images), len(existing_narrations)) if existing_narrations else len(existing_images)
        if n == 0:
            raise FileNotFoundError(
                f"No scene images (or narration) found in {run_dir}. "
                "Run without --use-existing first to generate them."
            )
        media_paths = [Path(p) for p in existing_images[:n]]
        audio_paths = [Path(p) for p in existing_narrations[:n]]
        if only_scene is not None:
            if only_scene < 1 or only_scene > n:
                raise IndexError(f"only_scene={only_scene} is out of range; have {n} scene(s) in {run_dir}.")
            idx = only_scene - 1
            media_paths = [media_paths[idx]]
            audio_paths = [audio_paths[idx]] if audio_paths else []
            n = 1
        if len(audio_paths) < n:
            raise FileNotFoundError(
                f"Found {len(media_paths)} scene(s) but only {len(audio_paths)} narration file(s) in {run_dir}. "
                "Need matching narration_001.mp3, narration_002.mp3, ..."
            )
        # Optional: turn existing scene images into short real-motion clips (recorded feel)
        if use_scene_video and media_paths:
            print("[Use existing] Converting scene images to real-motion video...")
            new_media = []
            for img_path in media_paths:
                video_path = Path(img_path).with_suffix(".scene.mp4")
                if video_path.exists():
                    new_media.append(video_path)
                else:
                    out_video = scene_video.scene_image_to_video(img_path, output_path=video_path)
                    new_media.append(out_video if out_video else img_path)
            media_paths = new_media
            if any(p.suffix.lower() == ".mp4" for p in media_paths):
                print("      -> Using real-motion clips where available.")
        print(f"[Use existing] Using {n} scene(s) and narration(s) from {run_dir}")
        print("[4/4] Composing video...")
        out_mp4 = output_dir / output_filename
        compose_video(
            scene_image_paths=media_paths,
            narration_audio_paths=audio_paths,
            output_path=out_mp4,
            scene_motion=True,
        )
        print(f"      -> Done: {out_mp4}")
        from .models import Scene
        dummy_scenes = [Scene(scene_number=i + 1, description="", narration_text="", duration_hint_sec=5.0) for i in range(n)]
        return out_mp4, SceneBreakdown(title="From existing run", scenes=dummy_scenes)

    # Resolve characters: from file or analyze from story
    chars: List[CharacterDescription] = []
    if characters_file and Path(characters_file).exists():
        chars = load_characters_from_file(Path(characters_file))
    elif analyze_characters or generate_character_images:
        chars = analyze_characters_from_story(story)
    character_descriptions = [f"{c.name}: {c.description}" for c in chars]

    # Optional: generate a standalone image per character (e.g. girl) from the scene
    if generate_character_images and chars:
        char_dir = run_dir / "characters"
        char_dir.mkdir(exist_ok=True)
        print(f"[0/4] Generating {len(chars)} character image(s) (e.g. girl, character from scene)...")
        for c in chars:
            generate_character_image(c.name, c.description, output_dir=char_dir)
        print(f"      -> Saved in {char_dir}")

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
        if character_descriptions:
            print(f"[2/4] Generating images (with {len(character_descriptions)} character hint(s))...")
        else:
            print("[2/4] Generating images...")
        for scene in breakdown.scenes:
            img_path = generate_scene_image(
                scene.description,
                scene.scene_number,
                output_dir=run_dir,
                character_descriptions=character_descriptions or None,
                visual_instruction=visual_instruction,
                movable=movable,
            )
            image_paths.append(img_path)

    # Optional: turn each scene image into a short video with real motion (feels like recorded video)
    media_paths: List[Path] = []
    if use_scene_video and image_paths:
        print("[2b/4] Converting scenes to video (real motion)...")
        for img_path in image_paths:
            video_path = scene_video.scene_image_to_video(
                img_path,
                output_path=Path(img_path).with_suffix(".scene.mp4"),
            )
            media_paths.append(video_path if video_path else img_path)
        if media_paths and any(p.suffix.lower() == ".mp4" for p in media_paths):
            print("      -> Some scenes use generated video clips.")
    if not media_paths:
        media_paths = image_paths

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
        scene_image_paths=media_paths,
        narration_audio_paths=audio_paths,
        output_path=out_mp4,
        scene_motion=True,
    )
    print(f"      -> Done: {out_mp4}")
    return out_mp4, breakdown
