from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Authentication Request Models
class LoginRequest(BaseModel):
    email: EmailStr

class CodeVerifyRequest(BaseModel):
    email: EmailStr
    code: str

class TokenConsumeRequest(BaseModel):
    code: str

# Authentication Response Models
class LoginResponse(BaseModel):
    message: str
    email: str
    expires_in_minutes: int

class CodeVerifyResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    full_name: Optional[str] = None
    profile_completed: bool = False
    is_admin: bool = False

class TokenConsumeResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    full_name: Optional[str] = None
    profile_completed: bool = False
    is_admin: bool = False

class UserProfile(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    profile_completed: bool = False

class MagicTokenRequest(BaseModel):
    token: str

class ProfileCompletionRequest(BaseModel):
    full_name: str
    department: str
    email: str

# GELİŞTİRME MODU: Direkt email ile giriş
class DevLoginRequest(BaseModel):
    email: EmailStr

# Request Models
class RequestCreate(BaseModel):
    original_text: str
    response_type: str  # positive, negative, informative, other
    is_new_request: bool = False  # Yeni istek öneri mi?

class GenerateRequest(BaseModel):
    request_id: int
    model_name: str
    custom_input: str
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    repetition_penalty: Optional[float] = 1.2
    system_prompt: Optional[str] = ""  # Sistem promptu eklendi

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

# Admin Models
class AdminStats(BaseModel):
    total_users: int
    total_requests: int
    total_responses: int
    total_tokens: int
    active_users_today: int
    requests_today: int

class UserStats(BaseModel):
    user_id: int
    email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    total_requests: int
    total_responses: int
    answered_requests: int  # Cevapladığı istek sayısı
    total_tokens: int
    last_activity: Optional[datetime] = None
    is_active: bool

class AdminUsersResponse(BaseModel):
    users: List[UserStats]
    total_count: int 