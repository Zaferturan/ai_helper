from fastapi import FastAPI
from connection import engine
import models
from endpoints import router
from auth_endpoints import auth_router

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="AI Helper API",
    description="AI Helper Backend API with Authentication",
    version="1.0.0"
)

# Include API endpoints
app.include_router(router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "AI Helper API çalışıyor"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 