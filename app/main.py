import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import documents, links, onboarding, workflow

app = FastAPI(
    title="POS / POS Referral Onboarding API",
    description="Backend for the digital onboarding flow (link generation, form, documents, approvals). Login/auth is provided by an existing system and is not part of this service.",
    version="1.0.0",
    root_path=settings.ROOT_PATH,
    servers=[
        {"url": settings.API_PUBLIC_URL, "description": "Production"},
        {"url": "http://localhost:8000", "description": "Local dev"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
if settings.STORAGE_BACKEND == "local":
    app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIR), name="files")

app.include_router(links.router)
app.include_router(onboarding.router)
app.include_router(documents.router)
app.include_router(workflow.router)


@app.get("/health")
def health():
    return {"status": "ok"}
