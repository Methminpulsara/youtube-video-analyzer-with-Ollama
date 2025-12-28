from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
import re


class AnalysisType(str, Enum):
    full = "full"
    summary_only = "summary_only"
    topics_only = "topics_only"
    insights_only = "insights_only"


# ---------- Helper models ----------

class VideoMetadata(BaseModel):
    title: Optional[str] = Field(
        None,
        description="Title of the YouTube video",
        example="How AI Will Change The World",
    )
    author: Optional[str] = Field(
        None,
        description="Channel or creator name",
        example="TechVision",
    )
    video_id: Optional[str] = Field(
        None,
        description="Extracted YouTube video ID",
        example="dQw4w9WgXcQ",
    )


class Topic(BaseModel):
    name: str = Field(
        ...,
        description="Identified topic name",
        min_length=2,
        max_length=100,
        example="Artificial Intelligence",
    )
    description: str = Field(
        ...,
        description="Explanation of the topic",
        min_length=5,
        max_length=500,
        example="Discussion about the role of AI in modern society.",
    )


class Insight(BaseModel):
    content: str = Field(
        ...,
        description="Insight or key takeaway",
        min_length=5,
        max_length=500,
        example="The speaker highlights the ethical concerns in using AI.",
    )
    type: str = Field(
        ...,
        description="Category of the insight",
        example="positive",
    )


class TranscriptChunk(BaseModel):
    index: int = Field(..., description="Chunk order index", example=0)
    text: str = Field(..., description="Part of the transcript")

class KeyMoment(BaseModel):
    timestamp: str = Field(..., description="Time marker (e.g. 02:30)")
    description: str = Field(..., description="Short summary of what happens at this time")

# ---------- Main request model ----------

class AnalysisRequest(BaseModel):
    youtube_url: str = Field(
        ...,
        description="Full YouTube video URL to analyze",
        example="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )
    analysis_type: AnalysisType = Field(
        default=AnalysisType.full,
        description="Type of analysis to perform",
    )

    @field_validator("youtube_url")
    def validate_youtube_url(cls, url: str):
        pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"
        if not re.match(pattern, url):
            raise ValueError("Invalid YouTube URL format")
        return url


# ---------- Main response model ----------

class AnalysisResponse(BaseModel):
    success: bool = Field(
        ...,
        description="Whether the analysis completed successfully",
    )
    transcript_chunks: List[TranscriptChunk] = Field(
        ...,
        description="Transcript split into small readable chunks",
    )
    topics: List[Topic] = Field(
        ...,
        description="List of extracted topics",
    )
    insights: List[Insight] = Field(
        ...,
        description="List of extracted insights",
    )
    summary: str = Field(
        ...,
        description="Summary generated from the full transcript",
    )
    processing_time: float = Field(
        ...,
        description="Time taken to complete processing (in seconds)",
        example=1.42,
    )
    metadata: Optional[VideoMetadata] = Field(
        None,
        description="Extra metadata about the video",
    )
    error: Optional[str] = Field(
        None,
        description="Error message if analysis failed",
        example="Transcript not available",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "transcript_chunks": [
                    {"index": 0, "text": "This is the beginning of the video..."},
                    {"index": 1, "text": "Next part of the transcript..."},
                ],
                "topics": [
                    {
                        "name": "AI",
                        "description": "Explanation about artificial intelligence in modern society.",
                    }
                ],
                "insights": [
                    {
                        "content": "AI is rapidly evolving and influencing all industries.",
                        "type": "positive",
                    }
                ],
                "summary": "This video explains the impact of AI on the future.",
                "processing_time": 1.23,
                "metadata": {
                    "title": "AI Future Explained",
                    "author": "TechVision",
                    "video_id": "abc123xyz",
                },
                "error": None,
            }
        }
    }
