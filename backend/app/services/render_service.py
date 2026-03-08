from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

logger = logging.getLogger(__name__)

RENDERS_DIR = Path(os.getenv("LOCAL_RENDER_ROOT", "/data/renders"))
RENDER_TIMEOUT = int(os.getenv("MANIM_RENDER_TIMEOUT", "300"))  # seconds


class RenderService:
    """Execute Manim code and produce a portrait MP4."""

    def render(self, slug: str, manim_code: str, scene_classes: list[str] | None = None) -> str:
        """
        Render Manim code into an MP4.
        Returns the absolute path of the final video file.
        """
        RENDERS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = RENDERS_DIR / f"{slug}.mp4"

        with tempfile.TemporaryDirectory(prefix="manim_") as tmpdir:
            tmpdir_path = Path(tmpdir)
            script_path = tmpdir_path / "scene.py"
            script_path.write_text(manim_code, encoding="utf-8")

            # Discover scene classes from code if not provided
            if not scene_classes:
                scene_classes = self._discover_scenes(manim_code)

            if not scene_classes:
                raise RuntimeError("No Scene subclasses found in generated Manim code")

            scene_videos: list[Path] = []
            for cls_name in scene_classes:
                video_path = self._render_scene(tmpdir_path, script_path, cls_name)
                if video_path and video_path.exists():
                    scene_videos.append(video_path)

            if not scene_videos:
                raise RuntimeError("Manim rendered no usable video files")

            if len(scene_videos) == 1:
                shutil.copy2(scene_videos[0], output_path)
            else:
                self._concatenate(scene_videos, output_path)

        logger.info("Rendered %s → %s", slug, output_path)
        return str(output_path)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _render_scene(
        self, workdir: Path, script_path: Path, cls_name: str
    ) -> Path | None:
        media_dir = workdir / "media"
        cmd = [
            "manim",
            "render",
            "--format", "mp4",
            "-ql",           # low quality for speed (480p); use -qm for 720p
            "--disable_caching",
            "--media_dir", str(media_dir),
            str(script_path),
            cls_name,
        ]
        logger.info("Running: %s", " ".join(cmd))
        try:
            result = subprocess.run(
                cmd,
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=RENDER_TIMEOUT,
            )
            if result.returncode != 0:
                logger.warning("Manim stderr for %s:\n%s", cls_name, result.stderr[-2000:])
                return None
        except subprocess.TimeoutExpired:
            logger.error("Manim timed out rendering %s", cls_name)
            return None
        except Exception as exc:
            logger.error("Manim failed for %s: %s", cls_name, exc)
            return None

        # Find the output mp4 in media/ recursively
        for mp4 in sorted(media_dir.rglob("*.mp4")):
            if cls_name in mp4.stem or "partial" not in mp4.parts:
                return mp4
        # Fallback: return any mp4
        mp4s = list(media_dir.rglob("*.mp4"))
        return mp4s[-1] if mp4s else None

    def _concatenate(self, videos: list[Path], output: Path) -> None:
        """Use ffmpeg concat demuxer to join scene videos."""
        list_path = output.parent / f"_concat_{int(time.time())}.txt"
        list_path.write_text(
            "\n".join(f"file '{v}'" for v in videos), encoding="utf-8"
        )
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(list_path),
            "-c", "copy",
            str(output),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)
        list_path.unlink(missing_ok=True)

    def _discover_scenes(self, code: str) -> list[str]:
        """Extract Scene subclass names from Manim source code."""
        import ast
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []
        classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = ""
                    if isinstance(base, ast.Name):
                        base_name = base.id
                    elif isinstance(base, ast.Attribute):
                        base_name = base.attr
                    if base_name == "Scene":
                        classes.append(node.name)
        return classes
