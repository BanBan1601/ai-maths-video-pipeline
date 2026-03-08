from __future__ import annotations

import json
from textwrap import dedent

import httpx

from app.core.config import settings


MANIM_SYSTEM_PROMPT = (
    "You are a Manim Community Edition code generator for vertical short-form math videos. "
    "Target: 1080x1920 (portrait). Dark background (#1a1a2e). High contrast text (#e0e0ff). "
    "IMPORTANT: Never use MathTex or Tex — always use Text() for all text and math notation. "
    "LaTeX is not available. Write math notation as plain Unicode strings inside Text(). "
    "One Scene subclass per beat. Keep animations short and clear."
)


class ManimGenerator:
    def __init__(self):
        self._ollama_url = settings.ollama_base_url
        self._model = settings.ollama_model

    def generate_from_scene_manifest(self, title: str, scenes: list[dict]) -> str:
        prompt = self._build_manim_prompt(title, scenes)
        try:
            code = self._call_ollama(prompt)
            code = self._extract_code(code)
            # Safety: strip any MathTex / Tex usage (fallback to Text)
            code = self._sanitize_latex(code)
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

        Rules (strictly follow all):
        - from manim import *
        - config.frame_width = 9 and config.frame_height = 16 at the top (portrait)
        - Background color "#1a1a2e" set in each construct() via self.camera.background_color
        - NEVER use MathTex or Tex — ONLY use Text() for all text including math notation
        - Write math like "f(x) = x^2" or "∑ 1/n²" directly as Text() strings
        - One class per scene: HookScene, DefinitionScene, IntuitionScene, TheoremScene, PayoffScene
        - Use VGroup with .arrange(DOWN, buff=0.5) for vertical stacking
        - Call fit_to_frame(group) before adding to scene
        - Text colors: headings "#4fc3f7", body "#e0e0ff", highlight "#ffd54f"
        - Each scene: FadeIn, self.wait(2-4 seconds), FadeOut
        - Output only valid Python code, no markdown fences.

        Include these helpers at the top after imports:
        def fit_to_frame(mob, max_width=7.0, max_height=13.0):
            if mob.width > max_width: mob.scale(max_width / mob.width)
            if mob.height > max_height: mob.scale(max_height / mob.height)
            return mob
        """).strip()

    def _call_ollama(self, prompt: str) -> str:
        response = httpx.post(
            f"{self._ollama_url}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "system": MANIM_SYSTEM_PROMPT,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 4096},
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

    def _sanitize_latex(self, code: str) -> str:
        """Replace MathTex/Tex with Text to avoid LaTeX dependency."""
        code = code.replace("MathTex(", "Text(")
        code = code.replace("Tex(", "Text(")
        return code

    def _fallback_manim(self, title: str, scenes: list[dict]) -> str:
        class_names = ["HookScene", "DefinitionScene", "IntuitionScene", "TheoremScene", "PayoffScene"]
        scene_classes = []

        for i, (scene, cls_name) in enumerate(zip(scenes[:5], class_names)):
            narration = scene.get("narration", f"Scene {i + 1}")
            # Split long narration into lines of ~50 chars
            words = narration.split()
            lines = []
            current = []
            for word in words:
                current.append(word)
                if len(" ".join(current)) > 45:
                    lines.append(" ".join(current))
                    current = []
            if current:
                lines.append(" ".join(current))
            # Cap at 3 lines
            lines = lines[:3]

            timing = scene.get("timing", f"0:{i*12:02d}-0:{(i+1)*12:02d}")
            safe_timing = timing.replace('"', "'")
            safe_lines = [l.replace('"', "'") for l in lines]

            text_items = "\n".join(
                f'            Text("{l}", color=TEXT_COLOR).scale(0.42),'
                for l in safe_lines
            )

            scene_classes.append(dedent(f'''
            class {cls_name}(Scene):
                def construct(self):
                    self.camera.background_color = BG_COLOR
                    label = Text("{safe_timing}", color=ACCENT_COLOR).scale(0.30)
                    body_items = [
            {text_items}
                    ]
                    group = VGroup(label, *body_items).arrange(DOWN, buff=0.35)
                    fit_to_frame(group)
                    self.play(FadeIn(group, shift=UP * 0.3))
                    self.wait(3)
                    self.play(FadeOut(group))
            ''').strip())

        classes_str = "\n\n\n".join(scene_classes)
        class_list = ", ".join(class_names[: len(scenes)])

        return dedent(f'''
        from manim import *

        config.frame_width = 9
        config.frame_height = 16

        BG_COLOR = "#1a1a2e"
        TEXT_COLOR = "#e0e0ff"
        ACCENT_COLOR = "#4fc3f7"
        HIGHLIGHT_COLOR = "#ffd54f"


        def fit_to_frame(mob, max_width=7.0, max_height=13.0):
            if mob.width > max_width:
                mob.scale(max_width / mob.width)
            if mob.height > max_height:
                mob.scale(max_height / mob.height)
            return mob


        # Title: {title}


        {classes_str}


        ALL_SCENES = [{class_list}]
        ''').strip()
