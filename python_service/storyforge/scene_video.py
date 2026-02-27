"""
Optional: turn each scene image into a short video with real motion (Stable Video Diffusion).
Makes scenes feel like recorded video with movement, not just a moving camera on a still.
Requires significant RAM/VRAM; falls back to normal image if SVD fails or is disabled.
"""
from pathlib import Path


def scene_image_to_video(
    image_path: Path,
    output_path: Path | None = None,
    num_frames: int = 14,
    fps: int = 7,
) -> Path | None:
    """
    Generate a short video from a single scene image using Stable Video Diffusion.
    Returns path to the generated video, or None if SVD fails or is unavailable.
    """
    image_path = Path(image_path)
    if not image_path.exists():
        return None
    output_path = output_path or image_path.with_suffix(".scene.mp4")
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        from diffusers import StableVideoDiffusionPipeline
        from diffusers.utils import load_image, export_to_video
    except ImportError:
        return None

    try:
        # Use CPU when no GPU/accelerator (enable_model_cpu_offload requires an accelerator)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cpu":
            pipe = StableVideoDiffusionPipeline.from_pretrained(
                "stabilityai/stable-video-diffusion-img2vid",
                torch_dtype=torch.float32,
            )
            pipe = pipe.to("cpu")
        else:
            pipe = StableVideoDiffusionPipeline.from_pretrained(
                "stabilityai/stable-video-diffusion-img2vid",
                torch_dtype=torch.float16,
                variant="fp16",
            )
            try:
                pipe.enable_model_cpu_offload()
            except Exception:
                pipe = pipe.to("cuda")
        if hasattr(pipe.unet, "enable_forward_chunking"):
            pipe.unet.enable_forward_chunking()
    except Exception as e:
        print(f"[SceneVideo] SVD load failed ({e}), using image + motion.")
        return None

    try:
        image = load_image(str(image_path))
        image = image.resize((1024, 576))
        generator = torch.manual_seed(42)
        out = pipe(image, decode_chunk_size=4, generator=generator)
        frames = out.frames[0] if hasattr(out, "frames") and out.frames else out[0]
        export_to_video(frames, str(output_path), fps=fps)
        return output_path
    except Exception as e:
        print(f"[SceneVideo] SVD generation failed ({e}), using image + motion.")
        return None
