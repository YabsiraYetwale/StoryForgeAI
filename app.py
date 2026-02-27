"""
StoryForge AI - Entry point for Hugging Face Spaces (free deployment).
Spaces run this file; it launches the Gradio app from python_service.
"""
import os
import sys

# Use placeholder images on free CPU Spaces (set IMAGE_BACKEND=huggingface for GPU Spaces)
if "IMAGE_BACKEND" not in os.environ:
    os.environ["IMAGE_BACKEND"] = "placeholder"

repo_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(repo_root, "python_service"))

from app_gradio import main

if __name__ == "__main__":
    main()
