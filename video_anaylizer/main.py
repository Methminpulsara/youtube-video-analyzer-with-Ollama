from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router

app = FastAPI(
    title="YouTube AI Analyzer API",
    description="AI-powered YouTube video content analysis with structured responses",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "YouTube AI Analyzer API - Structured Version",
        "version": "2.0.0",
        "endpoints": {
            "analyze": "POST /api/v1/analyze",
            "test": "GET /api/v1/test",
            "health": "GET /api/v1/health",
            "docs": "/docs",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
