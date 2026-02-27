"""
Video Composer: Images + narration audio → final MP4.
Adds cinematic motion per scene (zoom, pan) so it feels like recorded video, not static slides.
Optional: use image-to-video (Stable Video Diffusion) for real motion in each scene.
"""
from pathlib import Path
from typing import List, Tuple

from .config import OUTPUT_DIR, NARRATION_EXTRA_PAD_SEC

# Motion types applied in rotation so each scene feels different (like a moving camera)
MOTION_TYPES = ("zoom_in", "pan_right", "zoom_out", "pan_left", "zoom_plus_pan", "pan_slow")


def compose_video(
    scene_image_paths: List[Path],
    narration_audio_paths: List[Path],
    output_path: Path | None = None,
    fps: int = 24,
    add_silent_music: bool = False,
    scene_motion: bool = True,
) -> Path:
    """
    Compose a single MP4 from per-scene images and narration clips.
    scene_motion: if True, apply varied cinematic motion (zoom/pan) per scene so it feels like video.
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

    video_extensions = {".mp4", ".avi", ".mov", ".webm"}
    clips = []
    for idx, (media_path, audio_path) in enumerate(zip(scene_image_paths, narration_audio_paths)):
        media_path, audio_path = Path(media_path), Path(audio_path)
        if not media_path.exists():
            raise FileNotFoundError(f"Scene file not found: {media_path}")
        duration = _get_audio_duration(audio_path) + NARRATION_EXTRA_PAD_SEC
        duration = max(duration, 1.0)

        if media_path.suffix.lower() in video_extensions:
            try:
                from moviepy import VideoFileClip
            except ImportError:
                from moviepy.editor import VideoFileClip
            scene_clip = VideoFileClip(str(media_path))
            if scene_clip.duration < duration and scene_clip.duration > 0:
                scene_clip = _loop_clip_to_duration(scene_clip, duration)
            elif scene_clip.duration > duration:
                subfn = getattr(scene_clip, "subclipped", None) or getattr(scene_clip, "subclip", None)
                if subfn:
                    scene_clip = subfn(0, duration)
            scene_clip = _set_clip_duration(scene_clip, duration)
        else:
            image_clip = _set_clip_duration(ImageClip(str(media_path)), duration)
            if scene_motion:
                motion_type = MOTION_TYPES[idx % len(MOTION_TYPES)]
                scene_clip = _add_cinematic_motion(image_clip, duration, motion_type)
            else:
                scene_clip = _add_ken_burns_zoom(image_clip, duration)

        audio_clip = AudioFileClip(str(audio_path)) if audio_path.exists() else None
        if audio_clip is not None:
            scene_clip = _set_clip_audio(scene_clip, audio_clip)
        clips.append(scene_clip)

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


def _add_cinematic_motion(clip, duration: float, motion_type: str):
    """
    Add zoom and/or pan so each scene feels like a moving camera (recorded video feel).
    Varies by motion_type: zoom_in, zoom_out, pan_left, pan_right, zoom_plus_pan, pan_slow.
    """
    import numpy as np
    from PIL import Image

    zoom_factor = 0.15
    pan_factor = 0.08
    d = max(duration, 0.1)
    progress = lambda t: min(1.0, t / d)

    def transform(get_frame, t):
        frame = get_frame(t)
        if frame is None:
            return frame
        try:
            h, w = frame.shape[:2]
            p = progress(t)
            s = 1.0
            dx, dy = 0, 0
            if motion_type == "zoom_in":
                s = 1.0 + zoom_factor * p
            elif motion_type == "zoom_out":
                s = 1.0 + zoom_factor * (1.0 - p)
            elif motion_type == "pan_right":
                dx = int(w * pan_factor * p)
            elif motion_type == "pan_left":
                dx = -int(w * pan_factor * p)
            elif motion_type == "zoom_plus_pan":
                s = 1.0 + zoom_factor * 0.5 * p
                dx = int(w * pan_factor * 0.5 * p)
            elif motion_type == "pan_slow":
                dy = -int(h * pan_factor * 0.5 * p)
                s = 1.0 + zoom_factor * 0.3 * p
            else:
                s = 1.0 + zoom_factor * p
            new_w, new_h = int(w * s), int(h * s)
            pil = Image.fromarray(frame)
            pil = pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - w) // 2 - dx
            top = (new_h - h) // 2 - dy
            left = max(0, min(left, new_w - w))
            top = max(0, min(top, new_h - h))
            pil = pil.crop((left, top, left + w, top + h))
            return np.array(pil)
        except Exception:
            return frame

    try:
        return clip.fl(transform)
    except AttributeError:
        return clip.transform(transform)


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


def _loop_clip_to_duration(clip, duration: float):
    """Loop a short video clip until it fills the given duration."""
    try:
        from moviepy import concatenate_videoclips
    except ImportError:
        from moviepy.editor import concatenate_videoclips
    n_loops = int(duration / clip.duration) + 1
    if n_loops <= 1:
        return clip
    clips = [clip] * n_loops
    looped = concatenate_videoclips(clips, method="compose")
    subfn = getattr(looped, "subclipped", None) or getattr(looped, "subclip", None)
    return subfn(0, duration) if subfn else looped


def _get_audio_duration(audio_path: Path) -> float:
    """Return duration of audio file in seconds."""
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(str(audio_path))
        return len(seg) / 1000.0
    except Exception:
        return 5.0


def _set_clip_duration(clip, duration: float):
    """Compat helper: prefer set_duration, fallback to with_duration if present."""
    fn = getattr(clip, "set_duration", None) or getattr(clip, "with_duration", None)
    return fn(duration) if fn else clip


def _set_clip_audio(clip, audio_clip):
    """Compat helper: prefer set_audio, fallback to with_audio if present."""
    fn = getattr(clip, "set_audio", None) or getattr(clip, "with_audio", None)
    return fn(audio_clip) if fn else clip
