import os
import time
import logging
from typing import List, Optional
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# Schema imports
from ..models.schemas import (
    AnalysisResponse,
    Topic,
    Insight,
    VideoMetadata,
    AnalysisType,
    TranscriptChunk,
    KeyMoment  # අලුතින් add කළ එක
)
from .youtube_service import YouTubeService

load_dotenv()

logger = logging.getLogger("AnalysisService")
logger.setLevel(logging.INFO)


# --- LLM Response Schema (Updated) ---
class LLMResponseSchema(BaseModel):
    # Metadata fix කිරීම සඳහා
    title: str = Field(description="Most suitable title for the video")
    author: str = Field(description="Speaker or channel name")

    topics: List[Topic] = Field(description="List of key topics")
    insights: List[Insight] = Field(description="List of key insights")
    key_moments: List[KeyMoment] = Field(description="Key events with estimated timestamps")
    summary: str = Field(description="A comprehensive summary")


class AnalysisService:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.llm = ChatOpenAI(
            model=model,
            temperature=0,
            max_retries=2
        ).with_structured_output(LLMResponseSchema, strict=True)

        self.youtube_service = YouTubeService()
        self._setup_prompts()

    def _setup_prompts(self):
        self.analysis_prompt = ChatPromptTemplate.from_template(
            """
            Analyze the following YouTube transcript professionally.

            1. Suggest a clear Title and identify the Speaker/Channel (Author).
            2. Extract 3-5 main Topics.
            3. Extract key Insights (positive/negative/neutral).
            4. Identify 'Key Moments' - assign estimated timestamps based on transcript flow.
            5. Provide a high-quality Summary.

            Transcript:
            {transcript}
            """
        )

    async def analyze(self, youtube_url: str, mode: AnalysisType = AnalysisType.full):
        start_time = time.time()
        try:
            logger.info(f"Processing: {youtube_url}")

            video_data = await self.youtube_service.get_transcript_async(youtube_url)
            if not video_data["success"]:
                return self._error_response(video_data.get("error", "Transcript retrieval failed"), start_time)

            transcript_text = video_data["transcript"][:8000]

            # LLM Invoke
            chain = self.analysis_prompt | self.llm
            result: LLMResponseSchema = await chain.ainvoke({"transcript": transcript_text})

            # Metadata Optimization: YouTube එකෙන් එන්නේ නැත්නම් LLM එකෙන් එන දේ ගන්නවා
            metadata = VideoMetadata(
                title=video_data.get("video_title") if video_data.get("video_title") != "Unknown" else result.title,
                author=video_data.get("author") if video_data.get("author") != "Unknown" else result.author,
                video_id=video_data.get("video_id"),
            )

            transcript_chunks = self._split_transcript(transcript_text)

            return AnalysisResponse(
                success=True,
                transcript_chunks=transcript_chunks,
                topics=result.topics,
                insights=result.insights,
                key_moments=result.key_moments,  # අලුතින් එකතු විය
                summary=result.summary,
                metadata=metadata,
                processing_time=time.time() - start_time,
                error=None,
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return self._error_response(str(e), start_time)

    def _split_transcript(self, text: str, max_len: int = 400) -> List[TranscriptChunk]:
        import re
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        chunks, current, idx = [], "", 0
        for s in sentences:
            if len(current) + len(s) <= max_len:
                current += (" " if current else "") + s
            else:
                if current:
                    chunks.append(TranscriptChunk(index=idx, text=current))
                    idx += 1
                current = s
        if current: chunks.append(TranscriptChunk(index=idx, text=current))
        return chunks

    def _error_response(self, error_msg: str, start_time: float):
        return AnalysisResponse(
            success=False, transcript_chunks=[], topics=[], insights=[],
            summary="", metadata=None, processing_time=time.time() - start_time,
            error=error_msg
        )