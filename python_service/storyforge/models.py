"""Data models for scenes and pipeline."""
from pydantic import BaseModel, Field
from typing import List


class Scene(BaseModel):
    """A single scene in the story."""
    scene_number: int = Field(..., description="1-based scene index")
    description: str = Field(..., description="Visual description for image generation")
    narration_text: str = Field(..., description="Text to be spoken in this scene")
    duration_hint_sec: float = Field(default=5.0, description="Suggested duration in seconds")


class SceneBreakdown(BaseModel):
    """Full breakdown of a story into scenes."""
    title: str = Field(default="Untitled", description="Story title")
    scenes: List[Scene] = Field(default_factory=list, description="Ordered list of scenes")
