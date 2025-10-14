from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import api_models
from connection import get_db
from ollama_client import OllamaClient
from gemini_client import GeminiClient
from auth_endpoints import get_current_user
from models import User

router = APIRouter()
ollama_client = OllamaClient()
gemini_client = GeminiClient()

@router.get("/models", response_model=List[api_models.ModelInfo])
async def get_models(db: Session = Depends(get_db)):
    """Get available models from Ollama and Gemini, sync with database"""
    try:
        all_models = []
        
        # Get Ollama models
        try:
            ollama_models = ollama_client.get_available_models()
            for model_name in ollama_models:
                all_models.append({
                    "name": model_name,
                    "provider": "ollama"
                })
        except Exception as e:
            print(f"Ollama models error: {e}")
        
        # Get Gemini models
        try:
            gemini_models = gemini_client.get_available_models()
            for model_name in gemini_models:
                all_models.append({
                    "name": model_name,
                    "provider": "gemini"
                })
        except Exception as e:
            print(f"Gemini models error: {e}")
        
        # Sync with database
        for model_info in all_models:
            existing_model = db.query(models.Model).filter(
                models.Model.name == model_info["name"],
                models.Model.provider == model_info["provider"]
            ).first()
            
            if not existing_model:
                new_model = models.Model(
                    name=model_info["name"],
                    provider=model_info["provider"]
                )
                db.add(new_model)
        
        db.commit()
        
        return all_models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate", response_model=api_models.GenerateResponse)
async def generate_response(
    request: api_models.GenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate AI response using selected model"""
    try:
        # Create request record
        db_request = models.Request(
            user_id=current_user.id,
            original_text=request.original_text,
            custom_input=request.custom_input
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        
        # Generate responses
        responses = []
        for i in range(request.response_count):
            try:
                # Get model info
                model = db.query(models.Model).filter(
                    models.Model.name == request.model_name
                ).first()
                
                if not model:
                    raise HTTPException(status_code=404, detail=f"Model not found: {request.model_name}")
                
                # Generate response based on provider
                if model.provider == "ollama":
                    generated_text = ollama_client.generate(
                        model_name=request.model_name,
                        original_text=request.original_text,
                        custom_input=request.custom_input,
                        system_prompt=request.system_prompt,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        top_k=request.top_k
                    )
                elif model.provider == "gemini":
                    generated_text = gemini_client.generate(
                        model_name=request.model_name,
                        original_text=request.original_text,
                        custom_input=request.custom_input,
                        system_prompt=request.system_prompt,
                        temperature=request.temperature,
                        top_p=request.top_p,
                        top_k=request.top_k
                    )
                else:
                    raise HTTPException(status_code=400, detail=f"Unsupported provider: {model.provider}")
                
                # Create response record
                db_response = models.Response(
                    request_id=db_request.id,
                    model_id=model.id,
                    generated_text=generated_text,
                    has_been_copied=False
                )
                db.add(db_response)
                db.commit()
                db.refresh(db_response)
                
                responses.append({
                    "id": db_response.id,
                    "text": generated_text,
                    "model_name": request.model_name,
                    "has_been_copied": False
                })
            except Exception as e:
                print(f"Response generation error: {e}")
                responses.append({
                    "id": None,
                    "text": f"Hata: {str(e)}",
                    "model_name": request.model_name,
                    "has_been_copied": False
                })
        
        return {
            "request_id": db_request.id,
            "responses": responses
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/copy/{response_id}")
async def mark_response_copied(
    response_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a response as copied"""
    try:
        db_response = db.query(models.Response).filter(
            models.Response.id == response_id
        ).first()
        
        if not db_response:
            raise HTTPException(status_code=404, detail="Response not found")
        
        db_response.has_been_copied = True
        db.commit()
        
        return {"success": True, "message": "Response marked as copied"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=api_models.StatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get all users count
        total_users = db.query(models.User).count()
        
        # Get total requests
        total_requests = db.query(models.Request).count()
        
        # Get total responses
        total_responses = db.query(models.Response).count()
        
        # Get copied responses
        copied_responses = db.query(models.Response).filter(
            models.Response.has_been_copied == True
        ).count()
        
        # Get user-specific stats
        user_requests = db.query(models.Request).filter(
            models.Request.user_id == current_user.id
        ).count()
        
        user_responses = db.query(models.Response).join(models.Request).filter(
            models.Request.user_id == current_user.id
        ).count()
        
        user_copied = db.query(models.Response).join(models.Request).filter(
            models.Request.user_id == current_user.id,
            models.Response.has_been_copied == True
        ).count()
        
        return {
            "total_users": total_users,
            "total_requests": total_requests,
            "total_responses": total_responses,
            "copied_responses": copied_responses,
            "user_requests": user_requests,
            "user_responses": user_responses,
            "user_copied": user_copied
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-prompt")
async def get_system_prompt(
    current_user: User = Depends(get_current_user)
):
    """Get current system prompt"""
    try:
        with open("saved_system_prompt.txt", "r", encoding="utf-8") as f:
            system_prompt = f.read()
        return {"system_prompt": system_prompt}
    except FileNotFoundError:
        return {"system_prompt": ""}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/system-prompt")
async def save_system_prompt(
    request: api_models.SystemPromptRequest,
    current_user: User = Depends(get_current_user)
):
    """Save system prompt"""
    try:
        # Check if user is admin
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        with open("saved_system_prompt.txt", "w", encoding="utf-8") as f:
            f.write(request.system_prompt)
        
        return {"success": True, "message": "System prompt saved"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile")
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    """Get user profile"""
    return {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "department": current_user.department,
        "is_admin": current_user.is_admin,
        "profile_completed": current_user.profile_completed
    }

@router.post("/profile/complete")
async def complete_profile(
    request: api_models.ProfileCompleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Complete user profile"""
    try:
        current_user.full_name = request.full_name
        current_user.department = request.department
        current_user.profile_completed = True
        
        db.commit()
        
        return {
            "success": True,
            "message": "Profile completed",
            "full_name": current_user.full_name,
            "department": current_user.department
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session")
async def check_session(
    current_user: User = Depends(get_current_user)
):
    """Check if user has active session"""
    return {
        "authenticated": True,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "department": current_user.department,
        "is_admin": current_user.is_admin,
        "profile_completed": current_user.profile_completed
    }

