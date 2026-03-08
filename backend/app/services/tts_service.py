from __future__ import annotations

import asyncio
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(os.getenv("LOCAL_ASSET_ROOT", "/data/assets"))
EDGE_TTS_VOICE = os.getenv("TTS_VOICE", "en-US-JennyNeural")


class TTSService:
    """Generate narration audio using edge-tts (Microsoft Edge TTS — free, high quality)."""

    def synthesize(self, slug: str, script_data: dict) -> str:
        """
        Generate narration WAV from script scenes.
        Returns the absolute path of the MP3 file.
        """
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        output_mp3 = ASSETS_DIR / f"{slug}_narration.mp3"

        scenes = script_data.get("scenes", [])
        parts = [s.get("narration", "").strip() for s in scenes if s.get("narration")]
        full_text = " ... ".join(parts)

        if not full_text:
            raise RuntimeError("No narration text found in script")

        try:
            asyncio.run(self._edge_tts(full_text, str(output_mp3)))
            logger.info("TTS (edge-tts) saved: %s", output_mp3)
            return str(output_mp3)
        except Exception as exc:
            logger.warning("edge-tts failed: %s — falling back to espeak-ng", exc)
            output_wav = ASSETS_DIR / f"{slug}_narration.wav"
            self._espeak(full_text, str(output_wav))
            return str(output_wav)

    async def _edge_tts(self, text: str, output: str) -> None:
        import edge_tts
        tts = edge_tts.Communicate(text, voice=EDGE_TTS_VOICE)
        await tts.save(output)

    def _espeak(self, text: str, output: str) -> None:
        subprocess.run(
            ["espeak-ng", "-w", output, "--speed=150", text],
            check=True, capture_output=True, timeout=60,
        )
