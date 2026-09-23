from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from connection import engine
import models
from endpoints import router
from auth_endpoints import auth_router
from config import PRODUCTION_URL, FRONTEND_URL, ALLOWED_ORIGINS

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Helper API",
    description="AI Helper Backend API with Authentication",
    version="1.1.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

# CORS — explicit allowlist only (never "*"+credentials)
_origins = [o.strip() for o in ALLOWED_ORIGINS if o and o.strip()]
if not _origins:
    _origins = [PRODUCTION_URL, FRONTEND_URL]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "AI Helper API", "status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
