from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from connection import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)  # Artık zorunlu
    department = Column(String(255), nullable=False)  # Müdürlük bilgisi
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    profile_completed = Column(Boolean, default=False)  # Profil tamamlandı mı?
    is_admin = Column(Boolean, default=False)  # Admin yetkisi
    total_requests = Column(Integer, default=0)  # Toplam üretilen yanıt sayısı
    answered_requests = Column(Integer, default=0)  # Cevaplanan istek sayısı
    
    # Relationships
    login_attempts = relationship("LoginAttempt", back_populates="user")
    login_tokens = relationship("LoginToken", back_populates="user")
    requests = relationship("Request", back_populates="user")  # Kullanıcının istekleri
    template_categories = relationship("TemplateCategory", back_populates="owner")  # Kullanıcının kategorileri
    templates = relationship("Template", back_populates="owner")  # Kullanıcının şablonları

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False)  # IPv6 support
    success = Column(Boolean, nullable=False)
    method = Column(String(50), nullable=False)  # token, code
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="login_attempts")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_login_attempts_email_timestamp', 'email', 'timestamp'),
        Index('idx_login_attempts_ip_timestamp', 'ip_address', 'timestamp'),
    )

class LoginToken(Base):
    __tablename__ = "login_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String(255), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False, index=True)  # Token hash'i
    code_hash = Column(String(255), nullable=False, index=True)  # 6 haneli kod hash'i
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)  # Kullanıldığı zaman
    ip_created = Column(String(45), nullable=False)  # Oluşturulduğu IP
    user_agent_created = Column(String(500), nullable=True)  # Oluşturulduğu user agent
    attempt_count = Column(Integer, default=0)  # Deneme sayısı
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)  # Son deneme zamanı
    
    # Relationships
    user = relationship("User", back_populates="login_tokens")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_login_tokens_token_hash', 'token_hash'),
        Index('idx_login_tokens_code_hash', 'code_hash'),
        Index('idx_login_tokens_expires', 'expires_at'),
        Index('idx_login_tokens_email', 'email'),
    )

class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Hangi kullanıcının isteği
    original_text = Column(Text, nullable=False)
    response_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, nullable=True)  # Aktif istek mi?
    remaining_responses = Column(Integer, nullable=True)  # Kalan yanıt hakkı
    is_new_request = Column(Boolean, default=False)  # Yeni istek öneri mi?
    
    # Relationships
    user = relationship("User", back_populates="requests")
    responses = relationship("Response", back_populates="request")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    model_name = Column(String(100), ForeignKey("models.name"), nullable=False)
    response_text = Column(Text, nullable=False)
    temperature = Column(Float, nullable=False)
    top_p = Column(Float, nullable=False)
    repetition_penalty = Column(Float, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    is_selected = Column(Boolean, default=False)
    copied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tokens_used = Column(Integer, nullable=True)  # Kullanılan token sayısı
    
    # Relationships
    request = relationship("Request", back_populates="responses")
    model = relationship("Model", back_populates="responses")

class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(200), nullable=False)
    supports_embedding = Column(Boolean, default=False)
    supports_chat = Column(Boolean, default=False)
    
    # Relationship with Response table
    responses = relationship("Response", back_populates="model")

class TemplateCategory(Base):
    __tablename__ = "template_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(255), nullable=False, index=True)  # Departman bilgisi
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="template_categories")
    templates = relationship("Template", back_populates="category")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint('name', 'department', name='uq_category_name_department'),
        Index('idx_template_categories_department', 'department'),
        Index('idx_template_categories_owner', 'owner_user_id'),
    )

class Template(Base):
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    department = Column(String(255), nullable=False, index=True)  # Departman bilgisi
    owner_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("template_categories.id"), nullable=True)  # Kategori (opsiyonel)
    is_sms = Column(Boolean, default=False, index=True)  # SMS şablonu mu?
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)  # Soft delete için
    
    # Relationships
    owner = relationship("User", back_populates="templates")
    category = relationship("TemplateCategory", back_populates="templates")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_templates_department', 'department'),
        Index('idx_templates_category', 'category_id'),
        Index('idx_templates_owner', 'owner_user_id'),
        Index('idx_templates_active', 'is_active'),
        Index('idx_templates_created', 'created_at'),
        Index('idx_templates_is_sms', 'is_sms'),
    ) 