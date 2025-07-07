from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from llm_call.llm_api import router as llm_router
from therapist.th_api import router as therapist_router
import os

app = FastAPI(title="Aphasia AI API")


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

# Run via: uvicorn main:app --host 0.0.0.0 --port 7878 --reload
