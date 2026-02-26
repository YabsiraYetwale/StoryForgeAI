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
1. description: A clear, concrete visual description for AI image generation (setting, characters, action, mood, lighting). Be specific (e.g. "A young woman in a red dress stands in a sunlit market, baskets of fruit around her").
2. narration_text: The exact words to be spoken (voice-over) during this scene. Can be dialogue, description, or inner thought. Keep it concise for a 4-7 second clip.
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
    """Simple paragraph-based split when no LLM is configured."""
    paragraphs = [p.strip() for p in story.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [story[:500]] if story.strip() else ["A single scene."]
    scenes = []
    for i, para in enumerate(paragraphs[:10], start=1):
        excerpt = para[:200] + "..." if len(para) > 200 else para
        scenes.append(
            Scene(
                scene_number=i,
                description=f"Scene {i}: {excerpt}",
                narration_text=excerpt,
                duration_hint_sec=5.0,
            )
        )
    return SceneBreakdown(title="Untitled", scenes=scenes)
