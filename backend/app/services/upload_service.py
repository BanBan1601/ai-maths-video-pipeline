from __future__ import annotations


class UploadService:
    def youtube_status(self) -> dict:
        return {"enabled": True, "note": "Implement OAuth flow and YouTube upload adapter."}

    def instagram_status(self) -> dict:
        return {
            "enabled": False,
            "note": "Enable only after Graph API capability checks pass for the connected account.",
        }
