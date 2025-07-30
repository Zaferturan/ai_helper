from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from connection import Base

class Request(Base):
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    response_type = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with Response table
    responses = relationship("Response", back_populates="request")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    model_name = Column(String(100), ForeignKey("models.name"), nullable=False)
    response_text = Column(Text, nullable=False)
    latency_ms = Column(Float, nullable=True)
    is_selected = Column(Boolean, default=False)
    copied = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship with Request table
    request = relationship("Request", back_populates="responses")
    # Relationship with Model table
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