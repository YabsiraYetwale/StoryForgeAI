"""
Narration: Generate voice-over (TTS) for each scene.
Uses edge-tts (free, no API key) by default.
"""
import asyncio
from pathlib import Path
from .config import OUTPUT_DIR


async def _generate_tts_edge(text: str, output_path: Path, voice: str = "en-US-JennyNeural") -> Path:
    """Generate speech using Microsoft Edge TTS (free)."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    return output_path


def generate_narration_audio(
    narration_text: str,
    scene_number: int,
    output_dir: Path | None = None,
    voice: str = "en-US-JennyNeural",
) -> Path:
    """
    Generate TTS audio for a scene. Returns path to the saved MP3 file.
    """
    output_dir = output_dir or OUTPUT_DIR
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / f"narration_{scene_number:03d}.mp3"

    if not narration_text.strip():
        # Create silent audio (minimal file) so video composer doesn't break
        from pydub import AudioSegment
        silent = AudioSegment.silent(duration=1000)  # 1 sec
        silent.export(out_path, format="mp3")
        return out_path

    try:
        asyncio.run(_generate_tts_edge(narration_text, out_path, voice))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_generate_tts_edge(narration_text, out_path, voice))
    return out_path


def get_narration_duration_sec(audio_path: Path) -> float:
    """Return duration of an audio file in seconds."""
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(str(audio_path))
        return len(seg) / 1000.0
    except Exception:
        return 5.0
