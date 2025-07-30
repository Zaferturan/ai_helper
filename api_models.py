from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Request Models
class RequestCreate(BaseModel):
    original_text: str
    response_type: str  # positive, negative, informative, other

class GenerateRequest(BaseModel):
    request_id: int
    model_name: str
    custom_input: str
    citizen_name: Optional[str] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    repetition_penalty: Optional[float] = 1.2

class FeedbackRequest(BaseModel):
    response_id: int
    is_selected: bool
    copied: bool

# Response Models
class ModelInfo(BaseModel):
    name: str
    display_name: Optional[str] = None
    supports_embedding: Optional[bool] = None
    supports_chat: Optional[bool] = None

class RequestResponse(BaseModel):
    id: int
    original_text: str
    response_type: str
    created_at: datetime

class GenerateResponse(BaseModel):
    id: int
    request_id: int
    model_name: str
    response_text: str
    latency_ms: float
    created_at: datetime

class FeedbackResponse(BaseModel):
    success: bool
    message: str 