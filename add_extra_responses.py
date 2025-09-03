#!/usr/bin/env python3
import random
from datetime import datetime, timedelta
from connection import engine
from sqlalchemy.orm import Session
from models import User, Request, Response

def add_more_responses():
    session = Session(engine)
    
    # Kullanıcıları al (zafer hariç)
    users = session.query(User).filter(User.email != 'zaferturan@nilufer.bel.tr').all()
    
    print("Bazı isteklere ek cevaplar ekleniyor...")
    
    for user in users:
        # Bu kullanıcının isteklerini al
        requests = session.query(Request).filter(Request.user_id == user.id).all()
        
        if not requests:
            continue
            
        # Rastgele 3-5 isteğe ek cevap ekle
        num_extra_responses = random.randint(3, 5)
        selected_requests = random.sample(requests, min(num_extra_responses, len(requests)))
        
        print(f"{user.full_name}: {len(selected_requests)} isteğe ek cevap ekleniyor")
        
        for request in selected_requests:
            # Bu istek için kaç tane ek cevap ekleyeceğiz
            extra_count = random.randint(1, 3)
            
            for i in range(extra_count):
                response = Response(
                    request_id=request.id,
                    model_name="gemini-2.5-flash",
                    response_text=f"{user.full_name} ek cevap {i+1} - {request.original_text}",
                    temperature=0.5,
                    top_p=0.4,
                    repetition_penalty=2.0,
                    created_at=request.created_at + timedelta(minutes=random.randint(10, 120))
                )
                session.add(response)
    
    session.commit()
    print("Ek cevaplar eklendi!")
    session.close()

if __name__ == "__main__":
    add_more_responses()
