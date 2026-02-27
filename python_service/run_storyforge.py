#!/usr/bin/env python3
"""
StoryForge AI - Phase 1 CLI (Python service).
Run from project root: python run_storyforge.py "Your story text here"
Or:  python run_storyforge.py --file path/to/story.txt
Or from here: python python_service/run_storyforge.py ...
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add python_service to path so "from storyforge..." resolves
_SERVICE_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _SERVICE_DIR.parent
sys.path.insert(0, str(_SERVICE_DIR))

from storyforge.pipeline import run_pipeline


def _resolve_path(p: Path) -> Path:
    """Resolve relative paths: try python_service first, then project root."""
    if not p or p.is_absolute():
        return p
    in_service = _SERVICE_DIR / p
    in_root = _PROJECT_ROOT / p
    if in_service.exists():
        return in_service.resolve()
    # Use project root (so my_story.txt and image/ at repo root work from python_service)
    return in_root.resolve()


def main():
    parser = argparse.ArgumentParser(
        description="StoryForge AI: Transform a story into a cinematic video."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("story", nargs="?", help="Story text (inline)")
    group.add_argument("--file", "-f", type=Path, help="Path to a text file containing the story")
    group.add_argument("--use-existing", action="store_true", help="Use existing scenes and narration from output/run/ (only compose video, no story needed)")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory (default: ./output)",
    )
    parser.add_argument(
        "--name", "-n",
        type=str,
        default=None,
        help="Output video filename (default: storyforge_YYYY-MM-DD_HH-MM-SS.mp4 so each run is saved)",
    )
    parser.add_argument(
        "--voice", "-v",
        type=str,
        default="en-US-JennyNeural",
        help="TTS voice (edge-tts). Examples: en-US-JennyNeural, en-GB-SoniaNeural",
    )
    parser.add_argument(
        "--images", "-i",
        type=Path,
        default=None,
        metavar="DIR",
        help="Use images from this folder instead of generating. Files sorted by name (1.png, 2.png, ... or scene_01.jpg).",
    )
    parser.add_argument(
        "--characters", "-c",
        type=Path,
        default=None,
        metavar="FILE",
        help="JSON or text file with character descriptions (e.g. Maya: young woman, long brown hair). Used for consistent look in generated images.",
    )
    parser.add_argument(
        "--analyze-characters",
        action="store_true",
        help="Extract character descriptions from the story with AI (use when you don't provide --characters).",
    )
    parser.add_argument(
        "--visual-prompt", "-p",
        type=str,
        default=None,
        metavar="TEXT",
        help="Instruction for how scenes should look (e.g. 'young girl in focus, soft lighting, detailed environment'). Applied to every generated image.",
    )
    parser.add_argument(
        "--no-movable",
        action="store_true",
        help="Disable 'movable' hint (lifelike, dynamic) in image prompts. Default is movable=True.",
    )
    parser.add_argument(
        "--character-images",
        action="store_true",
        help="Generate a standalone image per character (e.g. girl) from the scene. Saves to output/run/characters/.",
    )
    parser.add_argument(
        "--animate-scenes",
        action="store_true",
        help="Turn each scene image into real-motion video (Stable Video Diffusion). With --use-existing, converts existing run/ images.",
    )
    parser.add_argument(
        "--only-scene",
        type=int,
        default=None,
        metavar="N",
        help="When using --use-existing, only use this 1-based scene index from output/run/ (e.g. 1 = scene_001).",
    )
    args = parser.parse_args()

    # Resolve paths so running from python_service finds repo files
    if args.use_existing:
        story = ""
    elif args.file:
        file_path = _resolve_path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {args.file} (tried {file_path})", file=sys.stderr)
            sys.exit(1)
        story = file_path.read_text(encoding="utf-8", errors="replace")
        args.file = file_path
    else:
        story = args.story or ""

    if not args.use_existing and not story.strip():
        print("Error: Story text is empty.", file=sys.stderr)
        sys.exit(1)

    if args.output is not None:
        args.output = _SERVICE_DIR / args.output if not args.output.is_absolute() else args.output
    else:
        args.output = _SERVICE_DIR / "output"

    if args.images is not None:
        args.images = _resolve_path(args.images)
        if not args.images.is_dir():
            print(f"Error: Images folder not found: {args.images}", file=sys.stderr)
            sys.exit(1)

    characters_file = None
    if args.characters is not None:
        characters_file = _resolve_path(args.characters)
        if not characters_file.exists():
            print(f"Error: Characters file not found: {args.characters}", file=sys.stderr)
            sys.exit(1)

    if args.name is None:
        args.name = f"storyforge_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"

    try:
        out_path, breakdown = run_pipeline(
            story=story,
            output_dir=args.output,
            output_filename=args.name,
            voice=args.voice,
            images_dir=args.images,
            characters_file=characters_file,
            analyze_characters=args.analyze_characters,
            visual_instruction=args.visual_prompt,
            movable=not args.no_movable,
            generate_character_images=args.character_images,
            use_scene_video=args.animate_scenes,
            use_existing_run=args.use_existing,
            only_scene=args.only_scene,
        )
        print(f"\nVideo saved: {out_path.resolve()}")
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
