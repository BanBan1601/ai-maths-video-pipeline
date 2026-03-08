from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TOKEN_PATH = Path("/data/youtube_token.json")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "http://localhost:8000/api/platforms/youtube/callback")


def _libs_available() -> bool:
    try:
        import google_auth_oauthlib  # noqa: F401
        import googleapiclient  # noqa: F401
        return True
    except ImportError:
        return False


class YouTubeService:
    def get_status(self) -> dict:
        if not CLIENT_ID or not CLIENT_SECRET:
            return {
                "connected": False,
                "reason": "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET not set in .env",
            }
        if not _libs_available():
            return {
                "connected": False,
                "reason": "google-api-python-client not installed (rebuild container)",
            }
        creds = self._load_token()
        if creds and creds.valid:
            return {"connected": True}
        if creds and creds.expired and creds.refresh_token:
            try:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
                self._save_token(creds)
                return {"connected": True}
            except Exception as e:
                return {"connected": False, "reason": f"Token refresh failed: {e}"}
        return {"connected": False, "reason": "Not authenticated — click Connect"}

    def get_auth_url(self) -> str:
        if not _libs_available():
            raise RuntimeError("google-auth-oauthlib not installed")
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uris": [REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url

    def exchange_code(self, code: str) -> None:
        if not _libs_available():
            raise RuntimeError("google-auth-oauthlib not installed")
        from google_auth_oauthlib.flow import Flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "redirect_uris": [REDIRECT_URI],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )
        flow.fetch_token(code=code)
        self._save_token(flow.credentials)

    def upload_video(
        self,
        file_path: str,
        title: str,
        description: str,
        tags: list[str],
        category_id: str = "27",  # "Education"
        scheduled_at: Optional[datetime] = None,
    ) -> dict:
        if not _libs_available():
            raise RuntimeError("google-api-python-client not installed")
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.auth.transport.requests import Request

        creds = self._load_token()
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                self._save_token(creds)
            else:
                raise RuntimeError("YouTube not authenticated — connect via /platforms")

        youtube = build("youtube", "v3", credentials=creds)

        status_body: dict = {"privacyStatus": "public"}
        if scheduled_at:
            # Must be in the future; YouTube requires RFC3339 UTC
            if scheduled_at.tzinfo is None:
                scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
            status_body["privacyStatus"] = "private"
            status_body["publishAt"] = scheduled_at.strftime("%Y-%m-%dT%H:%M:%SZ")

        body = {
            "snippet": {
                "title": title[:100],
                "description": description[:5000],
                "tags": tags[:500],
                "categoryId": category_id,
            },
            "status": status_body,
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/*")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

        response = None
        while response is None:
            _, response = request.next_chunk()

        video_id = response.get("id", "")
        return {
            "youtube_video_id": video_id,
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}",
            "scheduled": scheduled_at.isoformat() if scheduled_at else None,
        }

    # ── Token helpers ──────────────────────────────────────────────────────────

    def _load_token(self):
        if not TOKEN_PATH.exists():
            return None
        try:
            from google.oauth2.credentials import Credentials
            return Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
        except Exception:
            return None

    def _save_token(self, creds) -> None:
        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
        TOKEN_PATH.write_text(creds.to_json())
