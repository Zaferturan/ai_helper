#!/usr/bin/env python3
import random
from datetime import datetime, timedelta
from connection import engine
from sqlalchemy.orm import Session
from models import User, Request, Response

def fix_answered_requests():
    session = Session(engine)
    
    # Kullanıcıları al (zafer hariç)
    users = session.query(User).filter(User.email != 'zaferturan@nilufer.bel.tr').all()
    
    print("Cevapladığı istek sayılarını düzeltiyor...")
    
    for user in users:
        # Bu kullanıcının toplam yanıt sayısını al
        total_responses = session.query(Response).join(Request).filter(Request.user_id == user.id).count()
        
        # Cevapladığı istek sayısı toplam yanıtın yaklaşık yarısı olmalı
        target_answered = max(1, total_responses // 2)
        
        # Şu anda kaç istek cevaplanmış
        current_answered = session.query(Response).join(Request).filter(Request.user_id == user.id).distinct(Request.id).count()
        
        print(f"{user.full_name}: Toplam {total_responses} yanıt, hedef {target_answered} cevaplanmış istek")
        
        # Eğer hedef sayıya ulaşmamışsa, bazı isteklere cevap ekle
        if current_answered < target_answered:
            # Cevaplanmamış istekleri bul
            answered_requests = session.query(Request.id).join(Response).filter(Request.user_id == user.id).distinct().subquery()
            unanswered_requests = session.query(Request).filter(
                Request.user_id == user.id,
                ~Request.id.in_(answered_requests)
            ).all()
            
            # Rastgele isteklere cevap ekle
            to_answer = min(len(unanswered_requests), target_answered - current_answered)
            selected_requests = random.sample(unanswered_requests, to_answer)
            
            for request in selected_requests:
                response = Response(
                    request_id=request.id,
                    model_name="gemini-2.5-flash",
                    response_text=f"{user.full_name} cevap - {request.original_text}",
                    temperature=0.5,
                    top_p=0.4,
                    repetition_penalty=2.0,
                    created_at=request.created_at + timedelta(minutes=random.randint(5, 60))
                )
                session.add(response)
            
            print(f"  {to_answer} isteğe cevap eklendi")
    
    session.commit()
    print("Cevapladığı istek sayıları düzeltildi!")
    session.close()

if __name__ == "__main__":
    fix_answered_requests()
