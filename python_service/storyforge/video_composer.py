"""
Video Composer: Images + narration audio → final MP4.
Uses MoviePy to assemble scenes with voice-over and optional placeholder music.
"""
from pathlib import Path
from typing import List, Tuple

from .config import OUTPUT_DIR, NARRATION_EXTRA_PAD_SEC


def compose_video(
    scene_image_paths: List[Path],
    narration_audio_paths: List[Path],
    output_path: Path | None = None,
    fps: int = 24,
    add_silent_music: bool = False,
) -> Path:
    """
    Compose a single MP4 from per-scene images and narration clips.
    Each scene's duration is determined by the length of its narration + small padding.
    """
    try:
        from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
    except ImportError:
        from moviepy.editor import (
            ImageClip,
            AudioFileClip,
            concatenate_videoclips,
        )

    output_path = output_path or OUTPUT_DIR / "storyforge_output.mp4"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    clips = []
    for img_path, audio_path in zip(scene_image_paths, narration_audio_paths):
        img_path, audio_path = Path(img_path), Path(audio_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Scene image not found: {img_path}")
        duration = _get_audio_duration(audio_path) + NARRATION_EXTRA_PAD_SEC
        duration = max(duration, 1.0)
        image_clip = ImageClip(str(img_path)).with_duration(duration)
        image_clip = _add_ken_burns_zoom(image_clip, duration)
        audio_clip = AudioFileClip(str(audio_path)) if audio_path.exists() else None
        if audio_clip is not None:
            image_clip = image_clip.with_audio(audio_clip)
        clips.append(image_clip)

    if not clips:
        raise ValueError("No clips to compose")

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        str(output_path),
        fps=fps,
        codec="libx264",
        audio_codec="aac",
        temp_audiofile=str(output_path.parent / "_temp_audio.m4a"),
        remove_temp=True,
        logger=None,
    )
    for c in clips:
        c.close()
    final.close()
    return output_path


def _add_ken_burns_zoom(clip, duration: float, zoom_factor: float = 0.12):
    """Add a slow zoom-in (Ken Burns) so the image has subtle motion."""
    import numpy as np
    from PIL import Image

    def transform(get_frame, t):
        frame = get_frame(t)
        if frame is None:
            return frame
        try:
            h, w = frame.shape[:2]
            s = 1.0 + zoom_factor * min(1.0, t / max(duration, 0.1))
            new_w, new_h = int(w * s), int(h * s)
            pil = Image.fromarray(frame)
            pil = pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - w) // 2
            top = (new_h - h) // 2
            pil = pil.crop((left, top, left + w, top + h))
            return np.array(pil)
        except Exception:
            return frame

    try:
        return clip.fl(transform)
    except AttributeError:
        return clip.transform(transform)


def _get_audio_duration(audio_path: Path) -> float:
    """Return duration of audio file in seconds."""
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(str(audio_path))
        return len(seg) / 1000.0
    except Exception:
        return 5.0
