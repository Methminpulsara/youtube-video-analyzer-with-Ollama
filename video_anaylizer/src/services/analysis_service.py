import time
import json
import re
import logging
from typing import Dict, Any

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from ..models.schemas import (
    AnalysisResponse,
    Topic,
    Insight,
    VideoMetadata,
    AnalysisType,
)
from .youtube_service import YouTubeService


logger = logging.getLogger("AnalysisService")
logger.setLevel(logging.INFO)


class AnalysisService:
    def __init__(self, model: str = "llama3.2:3b"):
        self.llm = ChatOllama(model=model)
        self.youtube_service = YouTubeService()
        self._setup_prompts()

    # ---------------------------------------------
    # PROMPT SETUP
    # ---------------------------------------------
    def _setup_prompts(self):
        self.analysis_prompt = ChatPromptTemplate.from_template(
            """
            You are an expert content analyst. Return ONLY JSON. 
            No explanations. No markdown.

            Expected JSON format:
            {{
                "topics": [
                    {{
                        "name": "topic name",
                        "description": "topic description"
                    }}
                ],
                "insights": [
                    {{
                        "content": "insight content",
                        "type": "positive"
                    }}
                ],
                "summary": "summary content"
            }}

            Transcript:
            {transcript}
            """
        )

    # ---------------------------------------------
    # MAIN ANALYSIS FUNCTION
    # ---------------------------------------------
    async def analyze(self, youtube_url: str, mode: AnalysisType = AnalysisType.full):
        start_time = time.time()

        try:
            logger.info(f"Processing URL: {youtube_url}")

            # 1. LOAD TRANSCRIPT
            video_data = await self.youtube_service.get_transcript_async(youtube_url)

            if not video_data["success"]:
                return AnalysisResponse(
                    success=False,
                    transcript="",
                    topics=[],
                    insights=[],
                    summary="",
                    processing_time=time.time() - start_time,
                    metadata=None,
                    error=video_data["error"],
                )

            transcript = video_data["transcript"][:6000]  # Safety limit
            metadata = VideoMetadata(
                title=video_data.get("video_title"),
                author=video_data.get("author"),
                video_id=video_data.get("video_id"),
            )

            logger.info("Transcript loaded successfully")

            # 2. RUN LLM ANALYSIS
            chain = self.analysis_prompt | self.llm
            llm_result = chain.invoke({"transcript": transcript})
            raw_output = llm_result.content

            logger.info("LLM analysis completed")

            # 3. PARSE JSON
            parsed = self._extract_json(raw_output)

            topics = [Topic(**t) for t in parsed.get("topics", [])]
            insights = [Insight(**i) for i in parsed.get("insights", [])]
            summary = parsed.get("summary", "No summary available")

            elapsed = time.time() - start_time

            return AnalysisResponse(
                success=True,
                transcript=transcript,
                topics=topics,
                insights=insights,
                summary=summary,
                metadata=metadata,
                processing_time=elapsed,
                error=None,
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")

            return AnalysisResponse(
                success=False,
                transcript="",
                topics=[],
                insights=[],
                summary="",
                metadata=None,
                processing_time=time.time() - start_time,
                error=str(e),
            )

    # ---------------------------------------------
    # JSON EXTRACTION (bulletproof)
    # ---------------------------------------------
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract correct JSON from messy LLM output."""
        try:
            return json.loads(text)
        except:
            pass

        # Extract ```json blocks
        json_blocks = re.findall(r"```json(.*?)```", text, re.DOTALL)
        if json_blocks:
            try:
                return json.loads(json_blocks[0].strip())
            except:
                pass

        # Extract largest JSON-like structure
        brace_match = re.findall(r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}", text, re.DOTALL)
        for block in brace_match:
            try:
                return json.loads(block)
            except:
                continue

        # Fallback
        return {
            "topics": [],
            "insights": [],
            "summary": text[:300],
        }
