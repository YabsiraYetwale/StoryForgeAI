#!/usr/bin/env python3
"""Check if Hugging Face (Stable Diffusion) is available on this system."""
import sys

def main():
    print("Checking Hugging Face / Stable Diffusion setup...")
    print()
    print("Python:", sys.executable)
    print()

    ok = []
    missing = []
    for name in ["torch", "diffusers", "transformers", "PIL"]:
        try:
            __import__(name)
            ok.append(name)
        except ImportError:
            missing.append(name)

    if ok:
        print("Installed:", ", ".join(ok))
    if missing:
        print("Missing:  ", ", ".join(missing))
    print()

    if "torch" in ok:
        import torch
        print("PyTorch:  CUDA available =", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("          GPU:", torch.cuda.get_device_name(0))
    print()

    # Config
    try:
        from pathlib import Path
        _here = Path(__file__).resolve().parent
        if str(_here) not in sys.path:
            sys.path.insert(0, str(_here))
        from storyforge.config import IMAGE_BACKEND
        print("IMAGE_BACKEND (from .env):", IMAGE_BACKEND)
    except Exception as e:
        print("Config:", e)
    print()

    if not missing:
        print("Result:   Hugging Face (Stable Diffusion) is AVAILABLE.")
        print("          Set IMAGE_BACKEND=huggingface in .env to use real images.")
    else:
        print("Result:   Hugging Face is NOT fully installed.")
        print("          Run: pip install -r requirements.txt")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
