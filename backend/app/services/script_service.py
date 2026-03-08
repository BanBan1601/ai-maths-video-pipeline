from __future__ import annotations

import json
from textwrap import dedent
from typing import Optional

import httpx

from app.core.config import settings


SCRIPT_STRUCTURE = """
0–5s    Hook: surprising one-liner that makes the viewer stop scrolling
5–15s   Define the concept visually: one precise definition, shown not just stated
15–35s  Core intuition: the key geometric or conceptual insight, animated
35–50s  Key statement or proof sketch: one theorem or result made precise
50–60s  Payoff: why it matters, or a curiosity hook to follow
"""

SYSTEM_PROMPT = (
    "You are a mathematical script writer for 60-second educational short-form videos. "
    "Style: dark background, high contrast, minimal text, one idea per beat. "
    "Your scripts are factually precise, source-grounded, and visually driven. "
    "Never hallucinate mathematical facts. Label intuitions clearly as intuitions. "
    "Target: 130-155 spoken words total."
)


class ScriptService:
    def __init__(self):
        self._ollama_url = settings.ollama_base_url
        self._model = settings.ollama_model

    def build_short_script(
        self,
        title: str,
        video_type: str,
        idea_card: Optional[dict] = None,
        sources: Optional[list] = None,
    ) -> dict:
        """Build a layered 60-second script using Ollama, with fallback template."""
        source_context = ""
        if sources:
            source_context = "\n".join(
                f"- {s.get('title', s) if isinstance(s, dict) else s}" for s in sources[:3]
            )

        prompt = self._build_prompt(title, video_type, source_context, idea_card)

        try:
            result = self._call_ollama(prompt)
            script_data = self._parse_script(result, title, video_type)
        except Exception:
            script_data = self._fallback_script(title, video_type)

        script_data["sources_used"] = source_context
        return script_data

    def _build_prompt(
        self,
        title: str,
        video_type: str,
        source_context: str,
        idea_card: Optional[dict],
    ) -> str:
        hook_hint = ""
        if idea_card and idea_card.get("hook"):
            hook_hint = f'\nSuggested hook: "{idea_card["hook"]}"'

        return dedent(f"""
        Write a 60-second math short-form video script for: "{title}"
        Type: {video_type}
        {hook_hint}

        Structure (strictly follow timing):
        {SCRIPT_STRUCTURE}

        Academic sources available:
        {source_context or "Use standard mathematical references."}

        Output a JSON object with this exact structure:
        {{
          "hook": "...",
          "define_visual": "...",
          "core_intuition": "...",
          "key_statement": "...",
          "payoff": "...",
          "full_voiceover": "...",
          "word_count": 140,
          "scenes": [
            {{"scene_id": 1, "timing": "0-5s", "narration": "...", "visual_goal": "...", "math_objects": []}},
            {{"scene_id": 2, "timing": "5-15s", "narration": "...", "visual_goal": "...", "math_objects": []}},
            {{"scene_id": 3, "timing": "15-35s", "narration": "...", "visual_goal": "...", "math_objects": []}},
            {{"scene_id": 4, "timing": "35-50s", "narration": "...", "visual_goal": "...", "math_objects": []}},
            {{"scene_id": 5, "timing": "50-60s", "narration": "...", "visual_goal": "...", "math_objects": []}}
          ],
          "claims": [
            {{"text": "...", "type": "theorem|definition|intuition|historical", "needs_source": true}}
          ]
        }}

        Return only valid JSON, no markdown fences.
        """).strip()

    def _call_ollama(self, prompt: str) -> str:
        response = httpx.post(
            f"{self._ollama_url}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 2048},
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["response"]

    def _parse_script(self, raw: str, title: str, video_type: str) -> dict:
        # Try to extract JSON from response
        raw = raw.strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        data = json.loads(raw)
        voiceover = data.get("full_voiceover", "")
        word_count = len(voiceover.split()) if voiceover else data.get("word_count", 0)
        return {
            "title": title,
            "video_type": video_type,
            "hook": data.get("hook", ""),
            "define_visual": data.get("define_visual", ""),
            "core_intuition": data.get("core_intuition", ""),
            "key_statement": data.get("key_statement", ""),
            "payoff": data.get("payoff", ""),
            "full_voiceover": voiceover,
            "word_count": word_count,
            "duration_target_sec": 60,
            "scenes": data.get("scenes", []),
            "claims": data.get("claims", []),
            "generated_by": "ollama",
        }

    def _fallback_script(self, title: str, video_type: str) -> dict:
        """Template fallback when Ollama is unavailable."""
        hook = f"Here is something surprising about {title}."
        core = (
            "Start with one intuition, show one precise mathematical statement, "
            "then land one memorable consequence."
        )
        cta = "Follow for more visual maths."
        voiceover = f"{hook} {core} {cta}"
        return {
            "title": title,
            "video_type": video_type,
            "hook": hook,
            "define_visual": "Define the key concept with a precise statement.",
            "core_intuition": core,
            "key_statement": "State the main theorem clearly.",
            "payoff": cta,
            "full_voiceover": voiceover,
            "word_count": len(voiceover.split()),
            "duration_target_sec": 60,
            "scenes": [
                {
                    "scene_id": 1,
                    "timing": "0-5s",
                    "narration": hook,
                    "visual_goal": "Hook title card",
                    "math_objects": [],
                },
                {
                    "scene_id": 2,
                    "timing": "5-15s",
                    "narration": "Define the key concept.",
                    "visual_goal": "Definition box with formula",
                    "math_objects": [],
                },
                {
                    "scene_id": 3,
                    "timing": "15-35s",
                    "narration": core,
                    "visual_goal": "Animated geometric intuition",
                    "math_objects": [],
                },
                {
                    "scene_id": 4,
                    "timing": "35-50s",
                    "narration": "The main theorem.",
                    "visual_goal": "Theorem statement",
                    "math_objects": [],
                },
                {
                    "scene_id": 5,
                    "timing": "50-60s",
                    "narration": cta,
                    "visual_goal": "Payoff and end card",
                    "math_objects": [],
                },
            ],
            "claims": [{"text": title, "type": "intuition", "needs_source": False}],
            "generated_by": "fallback_template",
        }
