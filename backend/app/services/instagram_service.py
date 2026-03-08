from __future__ import annotations

import logging
import os
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
IG_USER_ID = os.getenv("INSTAGRAM_IG_USER_ID", "")
GRAPH_BASE = "https://graph.facebook.com/v19.0"


class InstagramService:
    def get_status(self) -> dict:
        if not ACCESS_TOKEN or not IG_USER_ID:
            return {
                "connected": False,
                "reason": "INSTAGRAM_ACCESS_TOKEN / INSTAGRAM_IG_USER_ID not set in .env",
            }
        # Quick ping to verify the token is still valid
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(
                    f"{GRAPH_BASE}/{IG_USER_ID}",
                    params={"fields": "id,username", "access_token": ACCESS_TOKEN},
                )
                data = resp.json()
                if "error" in data:
                    return {"connected": False, "reason": data["error"].get("message", "Invalid token")}
                return {"connected": True, "username": data.get("username", "")}
        except Exception as exc:
            return {"connected": False, "reason": str(exc)}

    def upload_video(
        self,
        video_url: str,  # must be a publicly accessible URL
        caption: str,
        scheduled_at=None,
    ) -> dict:
        """
        Upload a Reel to Instagram via Graph API (3-step: create container → await → publish).
        video_url must be publicly reachable (e.g. via ngrok or a CDN).
        """
        if not ACCESS_TOKEN or not IG_USER_ID:
            raise RuntimeError("Instagram credentials not configured")

        with httpx.Client(timeout=60) as client:
            # Step 1: Create media container
            params_create = {
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption[:2200],
                "access_token": ACCESS_TOKEN,
            }
            resp = client.post(f"{GRAPH_BASE}/{IG_USER_ID}/media", params=params_create)
            resp.raise_for_status()
            creation_id = resp.json().get("id")
            if not creation_id:
                raise RuntimeError(f"Container creation failed: {resp.text}")

            # Step 2: Poll until FINISHED (up to 3 minutes)
            for _ in range(36):
                time.sleep(5)
                status_resp = client.get(
                    f"{GRAPH_BASE}/{creation_id}",
                    params={"fields": "status_code", "access_token": ACCESS_TOKEN},
                )
                status_data = status_resp.json()
                status_code = status_data.get("status_code", "")
                if status_code == "FINISHED":
                    break
                if status_code == "ERROR":
                    raise RuntimeError(f"Instagram processing error: {status_data}")
            else:
                raise RuntimeError("Instagram container processing timed out")

            # Step 3: Publish
            resp_pub = client.post(
                f"{GRAPH_BASE}/{IG_USER_ID}/media_publish",
                params={"creation_id": creation_id, "access_token": ACCESS_TOKEN},
            )
            resp_pub.raise_for_status()
            media_id = resp_pub.json().get("id", "")
            return {
                "instagram_media_id": media_id,
                "instagram_url": f"https://www.instagram.com/p/{media_id}/",
            }
