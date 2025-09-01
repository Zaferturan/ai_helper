from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import api_models
from connection import get_db
from ollama_client import OllamaClient
from gemini_client import GeminiClient
from auth_endpoints import get_current_user

router = APIRouter()
ollama_client = OllamaClient()
gemini_client = GeminiClient()

@router.get("/models", response_model=List[api_models.ModelInfo])
async def get_models(db: Session = Depends(get_db)):
    """Get available models from Ollama and Gemini, sync with database"""
    try:
        all_models = []
        
        # Get models from Ollama
        print("DEBUG: Getting Ollama models...")
        ollama_models = ollama_client.get_models()
        print(f"DEBUG: Ollama models count: {len(ollama_models)}")
        print(f"DEBUG: Ollama models: {ollama_models}")
        all_models.extend(ollama_models)
        
        # Get models from Gemini
        print("DEBUG: Getting Gemini models...")
        gemini_models = await gemini_client.get_models()
        print(f"DEBUG: Gemini models count: {len(gemini_models)}")
        print(f"DEBUG: Gemini models: {gemini_models}")
        all_models.extend(gemini_models)
        
        print(f"DEBUG: Total models before DB sync: {len(all_models)}")
        
        # Sync with database
        for model_data in all_models:
            # Check if model exists in database
            existing_model = db.query(models.Model).filter(models.Model.name == model_data['name']).first()
            
            if existing_model:
                # Update existing model
                existing_model.display_name = model_data['display_name']
                existing_model.supports_embedding = model_data['supports_embedding']
                existing_model.supports_chat = model_data['supports_chat']
            else:
                # Create new model
                new_model = models.Model(
                    name=model_data['name'],
                    display_name=model_data['display_name'],
                    supports_embedding=model_data['supports_embedding'],
                    supports_chat=model_data['supports_chat']
                )
                db.add(new_model)
        
        db.commit()
        
        # Return models from database
        db_models = db.query(models.Model).all()
        print(f"DEBUG: DB models count: {len(db_models)}")
        return [
            api_models.ModelInfo(
                name=model.name,
                display_name=model.display_name,
                supports_embedding=model.supports_embedding,
                supports_chat=model.supports_chat
            )
            for model in db_models
        ]
    except Exception as e:
        print(f"DEBUG: Error in get_models: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

@router.post("/requests", response_model=api_models.RequestResponse)
async def create_request(request: api_models.RequestCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Create a new request"""
    try:
        # Validate response_type
        valid_types = ["positive", "negative", "informative", "other"]
        if request.response_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid response_type. Must be one of: {valid_types}")
        
        # Create new request
        new_request = models.Request(
            original_text=request.original_text,
            response_type=request.response_type,
            user_id=current_user.id,
            is_new_request=request.is_new_request  # Frontend'den gelen değer
        )
        
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        return api_models.RequestResponse(
            id=new_request.id,
            original_text=new_request.original_text,
            response_type=new_request.response_type,
            created_at=new_request.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating request: {str(e)}")

@router.put("/requests/{request_id}")
async def update_request(request_id: int, db: Session = Depends(get_db)):
    """Update request - GELİŞTİRME MODU: auth bypass"""
    try:
        # Request'i bul
        request = db.query(models.Request).filter(models.Request.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        # GELİŞTİRME MODU: auth bypass edildi
        
        # Bu endpoint artık sadece request'in varlığını kontrol ediyor
        db.commit()
        return {"message": "Request updated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating request: {str(e)}")

@router.put("/reset-copied-flags")
async def reset_copied_flags(db: Session = Depends(get_db)):
    """Reset copied flag for all responses - GELİŞTİRME MODU: auth bypass"""
    try:
        # Tüm response'ların copied flag'ini False yap
        db.query(models.Response).update({models.Response.copied: False})
        
        db.commit()
        return {"message": "All copied flags reset successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resetting copied flags: {str(e)}")

@router.put("/responses/{response_id}/mark-copied")
async def mark_response_as_copied(response_id: int, db: Session = Depends(get_db)):
    """Mark response as copied (copied=True) - GELİŞTİRME MODU: auth bypass"""
    try:
        # Response'u bul
        response = db.query(models.Response).filter(models.Response.id == response_id).first()
        if not response:
            raise HTTPException(status_code=404, detail="Response not found")

        # GELİŞTİRME MODU: auth bypass edildi
        
        # copied flag'ini True yap
        response.copied = True

        db.commit()
        return {"message": "Response marked as copied successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error marking response as copied: {str(e)}")

@router.get("/requests/{request_id}/has-copied-response")
async def check_request_has_copied_response(request_id: int, db: Session = Depends(get_db)):
    """Check if a request has any copied responses - GELİŞTİRME MODU: auth bypass"""
    try:
        # Request'i bul
        request = db.query(models.Request).filter(models.Request.id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")

        # GELİŞTİRME MODU: auth bypass edildi
        
        # Bu request için kopyalanmış yanıt var mı kontrol et
        has_copied_response = db.query(models.Response).filter(
            models.Response.request_id == request_id,
            models.Response.copied == True
        ).first() is not None

        return {"has_copied": has_copied_response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking request: {str(e)}")

@router.post("/generate", response_model=api_models.GenerateResponse)
async def generate_response(generate_request: api_models.GenerateRequest, db: Session = Depends(get_db)):
    """Generate response using Ollama"""
    try:
        # Get the original request
        original_request = db.query(models.Request).filter(models.Request.id == generate_request.request_id).first()
        if not original_request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Create prompt - daha kısa ve net
        prompt = f"""Vatandaş talebi: {original_request.original_text}

Personel cevabı: {generate_request.custom_input}

Bu cevabı genişlet, daha detaylı ve ikna edici hale getir."""
        
        # Sistem promptunu kullan (frontend'den gelen)
        system_prompt = generate_request.system_prompt if generate_request.system_prompt else ""
        
        # Determine which client to use based on model name
        if generate_request.model_name.startswith('gemini-'):
            # Use Gemini client
            response = await gemini_client.generate_response(
                generate_request.model_name, 
                prompt,
                temperature=generate_request.temperature,
                top_p=generate_request.top_p,
                repetition_penalty=generate_request.repetition_penalty,
                system_prompt=system_prompt  # Sistem promptunu geçir
            )
        else:
            # Use Ollama client
            response = await ollama_client.generate_response(
                generate_request.model_name, 
                prompt,
                temperature=generate_request.temperature,
                top_p=generate_request.top_p,
                repetition_penalty=generate_request.repetition_penalty,
                system_prompt=system_prompt  # Sistem promptunu geçir
            )
        
        if not response['success']:
            raise HTTPException(status_code=500, detail=f"Model error: {response['response_text']}")
        
        # Save response to database
        new_response = models.Response(
            request_id=generate_request.request_id,
            model_name=generate_request.model_name,
            response_text=response['response_text'],
            latency_ms=response['latency_ms']
        )
        
        db.add(new_response)
        db.commit()
        db.refresh(new_response)
        
        return api_models.GenerateResponse(
            id=new_response.id,
            request_id=new_response.request_id,
            model_name=new_response.model_name,
            response_text=new_response.response_text,
            latency_ms=new_response.latency_ms,
            created_at=new_response.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@router.post("/responses/feedback", response_model=api_models.FeedbackResponse)
async def update_response_feedback(feedback: api_models.FeedbackRequest, db: Session = Depends(get_db)):
    """Update response feedback (selected/copied status)"""
    try:
        # Find the response
        response = db.query(models.Response).filter(models.Response.id == feedback.response_id).first()
        if not response:
            raise HTTPException(status_code=404, detail="Response not found")
        
        # Update feedback
        response.is_selected = feedback.is_selected
        response.copied = feedback.copied
        
        db.commit()
        
        return api_models.FeedbackResponse(
            success=True,
            message="Feedback updated successfully",
            request_id=response.request_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating feedback: {str(e)}") 