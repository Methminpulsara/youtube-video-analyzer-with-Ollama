import re
import asyncio
from typing import Dict, Any

from langchain_community.document_loaders import YoutubeLoader


class YouTubeService:

    @staticmethod
    def extract_video_id(url: str) -> str | None:
        patterns = [
            r"(?:youtube\.com/watch\?v=|youtu\.be/)([^&/\?\n]+)",
            r"youtube\.com/embed/([^&/\?\n]+)",
            r"youtube\.com/v/([^&/\?\n]+)",
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def clean_youtube_url(url: str) -> str:
        vid = YouTubeService.extract_video_id(url)
        return f"https://www.youtube.com/watch?v={vid}" if vid else url

    # ---------------------------------------------
    # ASYNC VERSION
    # ---------------------------------------------
    async def get_transcript_async(self, url: str) -> Dict[str, Any]:
        """Loads transcript using fallback-safe async logic."""
        cleaned = self.clean_youtube_url(url)

        try:
            # FIRST TRY (full metadata)
            loader = YoutubeLoader.from_youtube_url(cleaned, add_video_info=True)
            docs = await asyncio.to_thread(loader.load)

            if docs:
                return {
                    "success": True,
                    "transcript": docs[0].page_content.strip(),
                    "video_title": docs[0].metadata.get("title", "Unknown"),
                    "author": docs[0].metadata.get("author", "Unknown"),
                    "video_id": self.extract_video_id(url),
                }

        except Exception:
            pass

        # SECOND TRY
        try:
            loader = YoutubeLoader.from_youtube_url(cleaned, add_video_info=False)
            docs = await asyncio.to_thread(loader.load)

            if docs:
                return {
                    "success": True,
                    "transcript": docs[0].page_content.strip(),
                    "video_title": "Unknown",
                    "author": "Unknown",
                    "video_id": self.extract_video_id(url),
                }

        except Exception as e:
            return {
                "success": False,
                "transcript": "",
                "video_title": "Unknown",
                "author": "Unknown",
                "error": f"Failed to load transcript: {str(e)}",
            }

        return {"success": False, "error": "Transcript not found"}
