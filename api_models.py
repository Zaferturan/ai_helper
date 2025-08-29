from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Authentication Models
class LoginRequest(BaseModel):
    email: EmailStr

class CodeVerifyRequest(BaseModel):
    email: EmailStr
    code: str

class TokenConsumeRequest(BaseModel):
    token: str

class LoginResponse(BaseModel):
    message: str
    success: bool

class CodeVerifyResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenConsumeResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

# User Profile Models
class UserProfile(BaseModel):
    id: int
    email: str
    name: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

# Legacy Models (for backward compatibility)
class Request(BaseModel):
    id: int
    original_text: str
    response_type: str
    created_at: datetime

class Response(BaseModel):
    id: int
    request_id: int
    model_name: str
    response_text: str
    latency_ms: Optional[float] = None
    is_selected: bool
    copied: bool
    created_at: datetime

class Model(BaseModel):
    id: int
    name: str
    display_name: str
    supports_embedding: bool
    supports_chat: bool 