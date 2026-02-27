"""
AI Scene Planner: Story → Scenes.
Uses an LLM to break a story into cinematic scenes with visual descriptions and narration.
"""
import json
from openai import OpenAI
from .config import OPENAI_API_KEY, OPENAI_API_BASE, SCENE_MODEL
from .models import SceneBreakdown, Scene

SYSTEM_PROMPT = """You are a cinematic scene planner for StoryForge AI. Your job is to break a written story into a sequence of visual scenes suitable for turning into a short film.

For each scene you must provide:
1. description: A clear, concrete visual description for AI image generation. Always include BOTH (a) the subject/character in the scene (e.g. a young girl, an old man) and (b) the environment and setting (e.g. sitting under a large oak tree, grass and flowers around, blue sky). Be specific so an AI can draw the full scene: character appearance, pose, location, lighting, mood. Example: "A young girl in a yellow dress sits under a large oak tree, dappled sunlight on her face, green grass and wildflowers around her, peaceful summer day."
2. narration_text: The exact words to be spoken (voice-over) during this scene. Keep it concise for a 4-7 second clip.
3. duration_hint_sec: Suggested duration in seconds (typically 4-8).

Output a JSON object with:
- "title": short story title
- "scenes": list of objects, each with "scene_number" (1-based), "description", "narration_text", "duration_hint_sec"

Create 3-8 scenes for short stories; for longer text, aim for one scene per major story beat. Be cinematic and visual."""


def plan_scenes(story: str) -> SceneBreakdown:
    """Break a story into scenes using the configured LLM."""
    if not OPENAI_API_KEY and not OPENAI_API_BASE:
        # Fallback: simple rule-based split for testing without API
        return _fallback_plan_scenes(story)

    client = OpenAI(api_key=OPENAI_API_KEY or "not-needed", base_url=OPENAI_API_BASE)
    user_content = f"Break this story into cinematic scenes.\n\nStory:\n{story}"

    response = client.chat.completions.create(
        model=SCENE_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.5,
    )
    text = response.choices[0].message.content.strip()
    # Extract JSON (handle markdown code blocks)
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    data = json.loads(text)
    return SceneBreakdown(**data)


def _fallback_plan_scenes(story: str) -> SceneBreakdown:
    """Split story into multiple scenes so the video tells the whole story (not just one image).
    Uses paragraphs first; if only one paragraph, splits by sentences into 3–8 scenes.
    """
    import re
    story = story.strip()
    if not story:
        return SceneBreakdown(title="Untitled", scenes=[
            Scene(scene_number=1, description="A single scene.", narration_text="A single scene.", duration_hint_sec=5.0)
        ])

    # Prefer paragraph split
    paragraphs = [p.strip() for p in story.split("\n\n") if p.strip()]
    if len(paragraphs) >= 2:
        # Multiple paragraphs → one scene per paragraph (max 10)
        chunks = paragraphs[:10]
    else:
        # Single paragraph → split by sentences so we get multiple scenes (storytelling)
        sentences = [s.strip() for s in re.split(r"[.!?]+", story) if s.strip()]
        if not sentences:
            chunks = [story[:400]]
        elif len(sentences) <= 3:
            chunks = sentences
        else:
            # Group 2–3 sentences per scene to get 3–8 scenes
            max_scenes = 8
            min_per_scene = max(1, len(sentences) // max_scenes)
            chunks = []
            current = []
            for s in sentences:
                current.append(s)
                if len(current) >= min_per_scene and len(chunks) < max_scenes - 1:
                    chunks.append(" ".join(current) + ".")
                    current = []
            if current:
                chunks.append(" ".join(current) + ("." if not current[-1].endswith(".") else ""))

    scenes = []
    for i, chunk in enumerate(chunks[:10], start=1):
        excerpt = (chunk[:220] + "...") if len(chunk) > 220 else chunk
        if not excerpt.endswith(".") and not excerpt.endswith("..."):
            excerpt = excerpt.rstrip() + "."
        scenes.append(
            Scene(
                scene_number=i,
                description=f"Scene {i}: {excerpt}",
                narration_text=excerpt,
                duration_hint_sec=5.0,
            )
        )
    return SceneBreakdown(title="Untitled", scenes=scenes)
