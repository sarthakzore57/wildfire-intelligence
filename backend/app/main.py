import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.api_v1.api import api_router
from app.core.config import settings
from app.services.firebase_service import init_firebase

init_firebase()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Serve static files (if needed)
static_files_dir = Path(__file__).parent / "static"
if static_files_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_files_dir)), name="static")

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to the Forest Fire Prediction System API",
        "docs": f"/docs",
        "version": "1.0.0",
    }

# Health check endpoint
@app.get("/health")
def health_check():
    try:
        _, firestore_db = init_firebase()
        db_status = "healthy" if firestore_db is not None else "unhealthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "ok",
        "database": db_status,
        "timestamp": time.time(),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 
