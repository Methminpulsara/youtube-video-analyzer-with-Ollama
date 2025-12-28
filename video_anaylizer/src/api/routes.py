from fastapi import APIRouter, Depends
from ..services.analysis_service import AnalysisService
from ..models.schemas import AnalysisRequest, AnalysisResponse, AnalysisType

router = APIRouter()

def get_service():
    return AnalysisService()


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_video(request: AnalysisRequest, service: AnalysisService = Depends(get_service)):
    return await service.analyze(request.youtube_url, request.analysis_type)


@router.get("/analyze/summary", response_model=AnalysisResponse)
async def analyze_summary(url: str, service: AnalysisService = Depends(get_service)):
    return await service.analyze(url, AnalysisType.summary_only)


@router.get("/analyze/topics", response_model=AnalysisResponse)
async def analyze_topics(url: str, service: AnalysisService = Depends(get_service)):
    return await service.analyze(url, AnalysisType.topics_only)


@router.get("/analyze/insights", response_model=AnalysisResponse)
async def analyze_insights(url: str, service: AnalysisService = Depends(get_service)):
    return await service.analyze(url, AnalysisType.insights_only)


@router.get("/debug/raw-llm")
async def debug_raw(url: str, service: AnalysisService = Depends(get_service)):
    data = await service.youtube_service.get_transcript_async(url)
    transcript = data["transcript"][:4000]

    chain = service._setup_prompts() | service.llm
    result = chain.invoke({"transcript": transcript})

    return {"raw_output": result.content}
