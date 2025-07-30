from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import api_models
from connection import get_db
from ollama_client import OllamaClient
from gemini_client import GeminiClient

router = APIRouter()
ollama_client = OllamaClient()
gemini_client = GeminiClient()

@router.get("/models", response_model=List[api_models.ModelInfo])
async def get_models(db: Session = Depends(get_db)):
    """Get available models from Ollama and Gemini, sync with database"""
    try:
        all_models = []
        
        # Get models from Ollama
        ollama_models = await ollama_client.get_models()
        all_models.extend(ollama_models)
        
        # Get models from Gemini
        gemini_models = await gemini_client.get_models()
        all_models.extend(gemini_models)
        
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
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

@router.post("/requests", response_model=api_models.RequestResponse)
async def create_request(request: api_models.RequestCreate, db: Session = Depends(get_db)):
    """Create a new request"""
    try:
        # Validate response_type
        valid_types = ["positive", "negative", "informative", "other"]
        if request.response_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid response_type. Must be one of: {valid_types}")
        
        # Create new request
        new_request = models.Request(
            original_text=request.original_text,
            response_type=request.response_type
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

@router.post("/generate", response_model=api_models.GenerateResponse)
async def generate_response(generate_request: api_models.GenerateRequest, db: Session = Depends(get_db)):
    """Generate response using Ollama"""
    try:
        # Get the original request
        original_request = db.query(models.Request).filter(models.Request.id == generate_request.request_id).first()
        if not original_request:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Create prompt
        prompt = f"Lütfen aşağıdaki metni kibar, resmi ve anlaşılır hale getir:\n\n{original_request.original_text}"
        
        # Determine which client to use based on model name
        if generate_request.model_name.startswith('gemini-'):
            # Use Gemini client
            response = await gemini_client.generate_response(
                generate_request.model_name, 
                prompt,
                citizen_name=generate_request.citizen_name,
                temperature=generate_request.temperature,
                top_p=generate_request.top_p,
                repetition_penalty=generate_request.repetition_penalty
            )
        else:
            # Use Ollama client
            response = await ollama_client.generate_response(
                generate_request.model_name, 
                prompt,
                citizen_name=generate_request.citizen_name,
                temperature=generate_request.temperature,
                top_p=generate_request.top_p,
                repetition_penalty=generate_request.repetition_penalty
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
            message="Feedback updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating feedback: {str(e)}") 