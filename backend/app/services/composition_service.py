from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

RENDERS_DIR = Path(os.getenv("LOCAL_RENDER_ROOT", "/data/renders"))
BGM_DIR = Path(os.getenv("DEFAULT_BGM_DIR", "/data/bgm"))
TARGET_W, TARGET_H = 1080, 1920   # 9:16 portrait


class CompositionService:
    """
    Compose the final video from:
      - Manim render (video, possibly with its own audio)
      - TTS narration WAV
      - Optional background music
    Output: a portrait 1080×1920 MP4 in /data/renders/{slug}_final.mp4
    """

    def compose(self, slug: str, video_path: str, audio_path: str | None) -> str:
        """
        Returns path to the composed final MP4.
        """
        RENDERS_DIR.mkdir(parents=True, exist_ok=True)
        final_path = RENDERS_DIR / f"{slug}_final.mp4"

        # Step 1 — scale to 9:16 portrait
        portrait_path = RENDERS_DIR / f"{slug}_portrait.mp4"
        self._scale_to_portrait(video_path, portrait_path)

        if audio_path and Path(audio_path).exists():
            # Step 2 — find optional BGM
            bgm_path = self._find_bgm()

            if bgm_path:
                # Step 3a — mix narration + BGM, then mux with video
                mixed_audio = RENDERS_DIR / f"{slug}_audio_mix.wav"
                self._mix_audio(audio_path, str(bgm_path), str(mixed_audio))
                self._mux(str(portrait_path), str(mixed_audio), str(final_path))
            else:
                # Step 3b — just mux narration with video
                self._mux(str(portrait_path), audio_path, str(final_path))

            portrait_path.unlink(missing_ok=True)
        else:
            # No audio — use the portrait video as-is
            portrait_path.rename(final_path)

        logger.info("Final video: %s", final_path)
        return str(final_path)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _scale_to_portrait(self, src: str, dst: Path) -> None:
        """Scale/pad video to 1080×1920 with dark background."""
        cmd = [
            "ffmpeg", "-y", "-i", src,
            "-vf", (
                f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio=decrease,"
                f"pad={TARGET_W}:{TARGET_H}:(ow-iw)/2:(oh-ih)/2:color=#1a1a2e"
            ),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",          # strip original audio (we'll mux narration)
            str(dst),
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)

    def _mux(self, video: str, audio: str, output: str) -> None:
        """Mux video with an audio track, trim to shorter of the two."""
        cmd = [
            "ffmpeg", "-y",
            "-i", video,
            "-i", audio,
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            output,
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=300)

    def _mix_audio(self, narration: str, bgm: str, output: str) -> None:
        """Mix narration (full volume) with BGM (ducked to 15%)."""
        cmd = [
            "ffmpeg", "-y",
            "-i", narration,
            "-i", bgm,
            "-filter_complex",
            "[1:a]volume=0.15,aloop=loop=-1:size=2e+09[bgm];[0:a][bgm]amix=inputs=2:duration=first[out]",
            "-map", "[out]",
            "-c:a", "pcm_s16le",
            output,
        ]
        subprocess.run(cmd, check=True, capture_output=True, timeout=120)

    def _find_bgm(self) -> Path | None:
        """Return the first .mp3/.wav found in BGM_DIR."""
        if not BGM_DIR.exists():
            return None
        for ext in ("*.mp3", "*.wav", "*.ogg"):
            files = list(BGM_DIR.glob(ext))
            if files:
                return files[0]
        return None
