from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from llm_call.llm_api import router as llm_router
from therapist.th_api import router as therapist_router
from backend.backend_api import router as backend_router
from backend.database import init_db
import os

app = FastAPI(title="Aphasia AI API")
init_db()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(llm_router, prefix="/api/llm", tags=["LLM Models"])
app.include_router(therapist_router, prefix="/api", tags=["Therapist QA"])
app.include_router(backend_router, prefix="/backend", tags=["Backend"])
# Run via: uvicorn main:app --host 0.0.0.0 --port 7878 --reload
