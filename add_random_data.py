#!/usr/bin/env python3
import random
from datetime import datetime, timedelta
from connection import engine
from sqlalchemy.orm import Session
from models import User, Request, Response

def add_random_data():
    session = Session(engine)
    
    # Kullanıcıları al (zafer hariç)
    users = session.query(User).filter(User.email != 'zaferturan@nilufer.bel.tr').all()
    
    print("Rastgele veriler ekleniyor...")
    
    for user in users:
        # Rastgele sayılar
        total_requests = random.randint(12, 25)
        answered_requests = random.randint(6, min(15, total_requests-1))
        
        print(f"{user.full_name}: {total_requests} istek, {answered_requests} cevap")
        
        # İstekleri ekle
        for i in range(total_requests):
            request = Request(
                user_id=user.id,
                original_text=f"{user.full_name} istek {i+1}",
                response_type="informative",
                created_at=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            session.add(request)
            session.flush()  # ID almak için
            
            # İlk answered_requests kadar cevap ekle
            if i < answered_requests:
                response = Response(
                    request_id=request.id,
                    model_name="gemini-2.5-flash",
                    response_text=f"{user.full_name} cevap {i+1}",
                    temperature=0.5,
                    top_p=0.4,
                    repetition_penalty=2.0,
                    created_at=request.created_at + timedelta(minutes=random.randint(5, 60))
                )
                session.add(response)
    
    session.commit()
    print("Tüm veriler eklendi!")
    session.close()

if __name__ == "__main__":
    add_random_data()
