from __future__ import annotations

import json
import logging
import os

import httpx

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")


class MetadataService:
    """Generate YouTube/Instagram metadata using the local Ollama LLM."""

    def generate(self, title: str, script_data: dict) -> dict:
        hook = script_data.get("hook", "")
        scenes_text = "\n".join(
            f"Scene {s.get('scene_id', i+1)}: {s.get('narration', '')}"
            for i, s in enumerate(script_data.get("scenes", []))
        )

        prompt = f"""You are a social media manager for a mathematics education channel.
Generate metadata for a 60-second math short-form video.

Video title: {title}
Hook: {hook}
Script summary:
{scenes_text}

Return ONLY valid JSON (no markdown, no explanation) with these exact keys:
{{
  "youtube_title": "Catchy title under 70 chars with a hook (include numbers or questions)",
  "youtube_description": "3-4 sentence description explaining the concept, who it's for, and a call to action. Include 2-3 hashtags at the end.",
  "instagram_caption": "Short punchy caption under 150 chars with 3-5 relevant hashtags",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8"],
  "category": "Education"
}}"""

        try:
            with httpx.Client(timeout=60) as client:
                resp = client.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                )
                resp.raise_for_status()
                raw = resp.json().get("response", "")
                # Strip markdown code fences if present
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                metadata = json.loads(raw.strip())
                return metadata
        except Exception as exc:
            logger.warning("Ollama metadata generation failed: %s — using fallback", exc)
            return self._fallback(title)

    def _fallback(self, title: str) -> dict:
        return {
            "youtube_title": f"{title} | 60-Second Math",
            "youtube_description": (
                f"In this short, we explore {title} — a key concept in mathematics. "
                "Whether you're a student or just curious, this 60-second breakdown "
                "will give you an intuitive understanding. Like and subscribe for more math! "
                "#mathematics #mathed #shorts"
            ),
            "instagram_caption": f"{title} explained in 60 seconds! 🧮 #math #mathshorts #education",
            "tags": ["mathematics", "math", "shorts", "education", "mathshorts", "stem", "learning", "manim"],
            "category": "Education",
        }
