from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import models
import api_models
from connection import get_db
from ollama_client import OllamaClient
from gemini_client import GeminiClient
from auth_endpoints import get_current_user
from models import User, Template, TemplateCategory

router = APIRouter()
ollama_client = OllamaClient()
gemini_client = GeminiClient()

@router.get("/models", response_model=List[api_models.ModelInfo])
async def get_models(db: Session = Depends(get_db)):
    """Get available models from Ollama and Gemini, sync with database"""
    try:
        all_models = []
        
        # Get models from Ollama
        ollama_models = ollama_client.get_models()
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
async def mark_response_as_copied(response_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Mark response as copied (copied=True) and increment answered_requests counter"""
    try:
        # Response'u bul
        response = db.query(models.Response).filter(models.Response.id == response_id).first()
        if not response:
            raise HTTPException(status_code=404, detail="Response not found")

        # copied flag'ini True yap
        response.copied = True
        
        # Kullanıcının answered_requests sayısını artır
        current_user.answered_requests += 1

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
        
        # Save response to database (store generation params for auditing)
        new_response = models.Response(
            request_id=generate_request.request_id,
            model_name=generate_request.model_name,
            response_text=response['response_text'],
            temperature=generate_request.temperature,
            top_p=generate_request.top_p,
            repetition_penalty=generate_request.repetition_penalty,
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

@router.get("/responses/history")
async def get_user_response_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Kullanıcının önceki yanıtlarını getir"""
    try:
        # Bu kullanıcının tüm request'lerini al
        user_requests = db.query(models.Request).filter(
            models.Request.user_id == current_user.id
        ).order_by(models.Request.created_at.desc()).offset(skip).limit(limit).all()
        
        # Her request için response'ları al
        responses = []
        for request in user_requests:
            request_responses = db.query(models.Response).filter(
                models.Response.request_id == request.id
            ).order_by(models.Response.created_at.desc()).all()
            
            for response in request_responses:
                responses.append({
                    'id': response.id,
                    'request_id': response.request_id,
                    'response_text': response.response_text,
                    'model_name': response.model_name,
                    'created_at': response.created_at.isoformat(),
                    'is_selected': response.is_selected,
                    'copied': response.copied,
                    'latency_ms': response.latency_ms
                })
        
        # En yeni response'lara göre sırala
        responses.sort(key=lambda x: x['created_at'], reverse=True)
        
        return {
            'success': True,
            'responses': responses,
            'total': len(responses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting response history: {str(e)}")

# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================

@router.get("/templates", response_model=api_models.TemplateListResponse)
async def get_templates(
    q: Optional[str] = Query(None, description="Arama terimi (başlık ve içerikte)"),
    category_id: Optional[int] = Query(None, description="Kategori ID'si"),
    only_mine: Optional[bool] = Query(False, description="Sadece kendi şablonlarım"),
    department: Optional[str] = Query(None, description="Departman filtresi (sadece admin)"),
    limit: int = Query(50, ge=1, le=100, description="Sayfa başına kayıt sayısı"),
    offset: int = Query(0, ge=0, description="Başlangıç kaydı"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Şablonları listele - departman bazlı filtreleme"""
    try:
        # Base query - departman filtresi zorunlu
        query = db.query(Template).filter(Template.is_active == True)
        
        # Departman filtresi
        if current_user.is_admin and department:
            # Admin belirli bir departman seçmişse
            query = query.filter(Template.department == department)
        elif not current_user.is_admin:
            # Admin değilse sadece kendi departmanını görebilir
            query = query.filter(Template.department == current_user.department)
        # Admin ama department parametresi yoksa tüm departmanları görebilir (mevcut davranış)
        
        # Arama filtresi (başlık ve içerikte)
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    Template.title.ilike(search_term),
                    Template.content.ilike(search_term)
                )
            )
        
        # Kategori filtresi
        if category_id:
            query = query.filter(Template.category_id == category_id)
        
        # Sadece kendi şablonlarım
        if only_mine:
            query = query.filter(Template.owner_user_id == current_user.id)
        
        # Toplam sayı
        total_count = query.count()
        
        # Sayfalama
        templates = query.order_by(Template.created_at.desc()).offset(offset).limit(limit).all()
        
        # Response formatına çevir
        template_responses = []
        for template in templates:
            # Owner bilgisi
            owner = db.query(User).filter(User.id == template.owner_user_id).first()
            owner_name = owner.full_name if owner else "Bilinmeyen"
            
            # Kategori bilgisi
            category_name = None
            if template.category_id:
                category = db.query(TemplateCategory).filter(TemplateCategory.id == template.category_id).first()
                category_name = category.name if category else None
            
            template_responses.append(api_models.TemplateResponse(
                id=template.id,
                title=template.title,
                content=template.content,
                department=template.department,
                owner_user_id=template.owner_user_id,
                owner_name=owner_name,
                category_id=template.category_id,
                category_name=category_name,
                created_at=template.created_at,
                updated_at=template.updated_at,
                is_active=template.is_active
            ))
        
        return api_models.TemplateListResponse(
            templates=template_responses,
            total_count=total_count,
            page=offset // limit + 1,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting templates: {str(e)}")

@router.post("/templates", response_model=api_models.TemplateResponse)
async def create_template(
    template_data: api_models.TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Yeni şablon oluştur"""
    try:
        # Title boşsa ilk 80 karakterden üret
        title = template_data.title
        if not title:
            title = template_data.content[:80] + "..." if len(template_data.content) > 80 else template_data.content
        
        # Kategori kontrolü (varsa)
        if template_data.category_id:
            category = db.query(TemplateCategory).filter(
                TemplateCategory.id == template_data.category_id,
                TemplateCategory.department == current_user.department
            ).first()
            
            if not category:
                raise HTTPException(status_code=404, detail="Kategori bulunamadı veya erişim yetkiniz yok")
        
        # Yeni şablon oluştur
        new_template = Template(
            title=title,
            content=template_data.content,
            department=current_user.department,
            owner_user_id=current_user.id,
            category_id=template_data.category_id
        )
        
        db.add(new_template)
        db.commit()
        db.refresh(new_template)
        
        # Response formatına çevir
        category_name = None
        if new_template.category_id:
            category = db.query(TemplateCategory).filter(TemplateCategory.id == new_template.category_id).first()
            category_name = category.name if category else None
        
        return api_models.TemplateResponse(
            id=new_template.id,
            title=new_template.title,
            content=new_template.content,
            department=new_template.department,
            owner_user_id=new_template.owner_user_id,
            owner_name=current_user.full_name,
            category_id=new_template.category_id,
            category_name=category_name,
            created_at=new_template.created_at,
            updated_at=new_template.updated_at,
            is_active=new_template.is_active
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating template: {str(e)}")

@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Şablon sil (soft delete) - sadece owner veya admin"""
    try:
        # Şablonu bul
        template = db.query(Template).filter(Template.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Şablon bulunamadı")
        
        # Departman kontrolü
        if not current_user.is_admin and template.department != current_user.department:
            raise HTTPException(status_code=403, detail="Bu şablona erişim yetkiniz yok")
        
        # Sahiplik kontrolü
        if not current_user.is_admin and template.owner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Sadece şablon sahibi silebilir")
        
        # Soft delete
        template.is_active = False
        db.commit()
        
        return {"success": True, "message": "Şablon başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting template: {str(e)}")

@router.put("/templates/{template_id}/use")
async def use_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Şablon kullanımını kaydet ve kullanıcının answered_requests sayısını artır"""
    try:
        # Şablonu bul
        template = db.query(Template).filter(
            Template.id == template_id,
            Template.is_active == True
        ).first()
        
        if not template:
            raise HTTPException(status_code=404, detail="Şablon bulunamadı")
        
        # Departman kontrolü
        if not current_user.is_admin and template.department != current_user.department:
            raise HTTPException(status_code=403, detail="Bu şablona erişim yetkiniz yok")
        
        # Kullanıcının answered_requests sayısını artır
        current_user.answered_requests += 1
        db.commit()
        
        return {"success": True, "message": "Şablon kullanımı kaydedildi"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error using template: {str(e)}")

# ============================================================================
# CATEGORY ENDPOINTS
# ============================================================================

@router.get("/categories", response_model=api_models.CategoryListResponse)
async def get_categories(
    department: Optional[str] = Query(None, description="Departman filtresi (sadece admin)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kategorileri listele - departman bazlı filtreleme"""
    try:
        # Base query - departman filtresi zorunlu
        query = db.query(TemplateCategory)
        
        # Departman filtresi
        if current_user.is_admin and department:
            # Admin belirli bir departman seçmişse
            query = query.filter(TemplateCategory.department == department)
        elif not current_user.is_admin:
            # Admin değilse sadece kendi departmanını görebilir
            query = query.filter(TemplateCategory.department == current_user.department)
        # Admin ama department parametresi yoksa tüm departmanları görebilir (mevcut davranış)
        
        categories = query.order_by(TemplateCategory.name).all()
        
        # Response formatına çevir
        category_responses = []
        for category in categories:
            # Owner bilgisi
            owner = db.query(User).filter(User.id == category.owner_user_id).first()
            owner_name = owner.full_name if owner else "Bilinmeyen"
            
            # Bu kategorideki şablon sayısı
            template_count = db.query(Template).filter(
                Template.category_id == category.id,
                Template.is_active == True
            ).count()
            
            # Mevcut kullanıcı owner mı?
            is_owner = category.owner_user_id == current_user.id
            
            category_responses.append(api_models.CategoryResponse(
                id=category.id,
                name=category.name,
                department=category.department,
                owner_user_id=category.owner_user_id,
                owner_name=owner_name,
                is_owner=is_owner,
                created_at=category.created_at,
                template_count=template_count
            ))
        
        return api_models.CategoryListResponse(
            categories=category_responses,
            total_count=len(category_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting categories: {str(e)}")

@router.post("/categories", response_model=api_models.CategoryResponse)
async def create_category(
    category_data: api_models.CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Yeni kategori oluştur - departman bazlı unique constraint"""
    try:
        # Aynı departmanda aynı isimde kategori var mı kontrol et
        existing_category = db.query(TemplateCategory).filter(
            TemplateCategory.name == category_data.name,
            TemplateCategory.department == current_user.department
        ).first()
        
        if existing_category:
            raise HTTPException(
                status_code=400, 
                detail=f"'{category_data.name}' isimli kategori zaten mevcut"
            )
        
        # Yeni kategori oluştur
        new_category = TemplateCategory(
            name=category_data.name,
            department=current_user.department,
            owner_user_id=current_user.id
        )
        
        db.add(new_category)
        db.commit()
        db.refresh(new_category)
        
        # Response formatına çevir
        return api_models.CategoryResponse(
            id=new_category.id,
            name=new_category.name,
            department=new_category.department,
            owner_user_id=new_category.owner_user_id,
            owner_name=current_user.full_name,
            is_owner=True,
            created_at=new_category.created_at,
            template_count=0  # Yeni kategori, henüz şablon yok
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating category: {str(e)}")

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Kategori sil - sadece owner veya admin, içinde şablon varsa engelle"""
    try:
        # Kategoriyi bul
        category = db.query(TemplateCategory).filter(TemplateCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Kategori bulunamadı")
        
        # Departman kontrolü
        if not current_user.is_admin and category.department != current_user.department:
            raise HTTPException(status_code=403, detail="Bu kategoriye erişim yetkiniz yok")
        
        # Sahiplik kontrolü
        if not current_user.is_admin and category.owner_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Sadece kategori sahibi silebilir")
        
        # İçinde aktif şablon var mı kontrol et
        active_templates_count = db.query(Template).filter(
            Template.category_id == category_id,
            Template.is_active == True
        ).count()
        
        if active_templates_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Bu kategoride {active_templates_count} adet şablon bulunuyor. Önce şablonları silin veya başka kategoriye taşıyın."
            )
        
        # Kategoriyi sil
        db.delete(category)
        db.commit()
        
        return {"success": True, "message": "Kategori başarıyla silindi"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting category: {str(e)}")

# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@router.get("/admin/departments")
async def get_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Departman listesi - sadece admin"""
    try:
        if not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
        
        # Distinct departman listesi
        departments = db.query(User.department).distinct().filter(
            User.department.isnot(None),
            User.department != ""
        ).order_by(User.department).all()
        
        department_list = [dept[0] for dept in departments]
        
        return {
            "departments": department_list,
            "total_count": len(department_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting departments: {str(e)}") 