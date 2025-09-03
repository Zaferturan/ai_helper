#!/usr/bin/env python3
import random
from datetime import datetime, timedelta
from connection import engine
from sqlalchemy.orm import Session
from models import User, Request, Response

def add_more_total_responses():
    session = Session(engine)
    
    # Kullanıcıları al (zafer hariç)
    users = session.query(User).filter(User.email != 'zaferturan@nilufer.bel.tr').all()
    
    print("Toplam yanıt sayılarını artırıyor...")
    
    for user in users:
        # Bu kullanıcının mevcut isteklerini al
        requests = session.query(Request).filter(Request.user_id == user.id).all()
        
        if not requests:
            continue
            
        # Her istek için 2-4 ek cevap ekle
        for request in requests:
            extra_count = random.randint(2, 4)
            
            for i in range(extra_count):
                response = Response(
                    request_id=request.id,
                    model_name="gemini-2.5-flash",
                    response_text=f"{user.full_name} ek yanıt {i+1} - {request.original_text}",
                    temperature=0.5,
                    top_p=0.4,
                    repetition_penalty=2.0,
                    created_at=request.created_at + timedelta(minutes=random.randint(5, 180))
                )
                session.add(response)
        
        print(f"{user.full_name}: {len(requests)} isteğe {extra_count} ek yanıt eklendi")
    
    session.commit()
    print("Toplam yanıt sayıları artırıldı!")
    session.close()

if __name__ == "__main__":
    add_more_total_responses()
