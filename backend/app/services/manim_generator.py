from __future__ import annotations

import json
from textwrap import dedent
from typing import Optional

import httpx

from app.core.config import settings


MANIM_SYSTEM_PROMPT = (
    "You are a Manim Community Edition code generator for vertical short-form math videos. "
    "Target: 1080x1920 (portrait). Dark background (#1a1a2e). High contrast text (#e0e0ff). "
    "Use safe layout helpers. Never use hardcoded pixel coordinates. "
    "One scene class per logical beat. All text from approved script only."
)


class ManimGenerator:
    def __init__(self):
        self._ollama_url = settings.ollama_base_url
        self._model = settings.ollama_model

    def generate_from_scene_manifest(self, title: str, scenes: list[dict]) -> str:
        """Generate complete Manim Python file from scene manifest."""
        prompt = self._build_manim_prompt(title, scenes)
        try:
            code = self._call_ollama(prompt)
            code = self._extract_code(code)
            return code
        except Exception:
            return self._fallback_manim(title, scenes)

    def _build_manim_prompt(self, title: str, scenes: list[dict]) -> str:
        scene_desc = json.dumps(scenes, indent=2)
        return dedent(f"""
        Generate complete Manim Community Edition Python code for a 60-second math short.

        Title: "{title}"

        Scene manifest:
        {scene_desc}

        Requirements:
        - from manim import *
        - Portrait frame: config.frame_width = 9, config.frame_height = 16
        - Background color: "#1a1a2e"
        - Text color: "#e0e0ff"
        - Accent color: "#4fc3f7"
        - One class per scene (HookScene, DefinitionScene, IntuitionScene, TheoremScene, PayoffScene)
        - Use VGroup with .arrange(DOWN, buff=0.3) for layout
        - Use .scale() to fit content, never hard-code coordinates
        - All text comes exactly from narration field in scene manifest
        - Each scene ends with self.wait() for timing
        - Include a render() function at bottom:
          def render():
              for cls in [HookScene, DefinitionScene, IntuitionScene, TheoremScene, PayoffScene]:
                  scene = cls()
                  scene.render()

        Output only valid Python code, no markdown fences.
        """).strip()

    def _call_ollama(self, prompt: str) -> str:
        response = httpx.post(
            f"{self._ollama_url}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "system": MANIM_SYSTEM_PROMPT,
                "stream": False,
                "options": {"temperature": 0.4, "num_predict": 4096},
            },
            timeout=180.0,
        )
        response.raise_for_status()
        return response.json()["response"]

    def _extract_code(self, raw: str) -> str:
        raw = raw.strip()
        if "```python" in raw:
            start = raw.find("```python") + 9
            end = raw.find("```", start)
            return raw[start:end].strip()
        if "```" in raw:
            start = raw.find("```") + 3
            end = raw.find("```", start)
            return raw[start:end].strip()
        return raw

    def _fallback_manim(self, title: str, scenes: list[dict]) -> str:
        """Generate a basic working Manim file when Ollama is unavailable."""
        scene_classes = []
        class_names = [
            "HookScene",
            "DefinitionScene",
            "IntuitionScene",
            "TheoremScene",
            "PayoffScene",
        ]
        for i, (scene, cls_name) in enumerate(zip(scenes[:5], class_names)):
            narration = scene.get("narration", scene.get("visual_goal", f"Scene {i + 1}"))[:80]
            # Escape any double-quotes in narration to avoid Python syntax errors
            narration_escaped = narration.replace('"', '\\"')
            timing = scene.get("timing", f"Scene {i + 1}")
            scene_classes.append(
                dedent(f'''
                class {cls_name}(Scene):
                    def construct(self):
                        self.camera.background_color = "#1a1a2e"
                        label = Text("{timing}", color="#4fc3f7").scale(0.35)
                        content = Text("{narration_escaped}", color="#e0e0ff").scale(0.45)
                        group = VGroup(label, content).arrange(DOWN, buff=0.4)
                        fit_to_frame(group)
                        keep_above_caption_zone(group)
                        self.play(FadeIn(group))
                        self.wait(2)
                        self.play(FadeOut(group))
                ''').strip()
            )

        classes_str = "\n\n".join(scene_classes)
        class_list = ", ".join(class_names[: len(scenes)])
        return dedent(f'''
        from manim import *

        BG_COLOR = "#1a1a2e"
        TEXT_COLOR = "#e0e0ff"
        ACCENT_COLOR = "#4fc3f7"
        HIGHLIGHT_COLOR = "#ffd54f"
        CAPTION_SAFE_BOTTOM = 0.15


        def fit_to_frame(mob, max_width=6.5, max_height=12.0):
            if mob.width > max_width:
                mob.scale(max_width / mob.width)
            if mob.height > max_height:
                mob.scale(max_height / mob.height)
            return mob


        def keep_above_caption_zone(mob, frame_height=14.0):
            min_y = -frame_height / 2 + frame_height * CAPTION_SAFE_BOTTOM + mob.height / 2
            if mob.get_bottom()[1] < min_y:
                mob.shift(UP * (min_y - mob.get_bottom()[1]))
            return mob


        # Title: {title}

        {classes_str}


        if __name__ == "__main__":
            import subprocess
            for cls in [{class_list}]:
                subprocess.run(["manim", "-pql", __file__, cls.__name__])
        ''').strip()
