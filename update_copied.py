#!/usr/bin/env python3
from connection import engine
from sqlalchemy.orm import Session
from models import User, Request, Response
import random

def update_copied():
    session = Session(engine)
    
    # Kullanıcıları al (zafer hariç)
    users = session.query(User).filter(User.email != 'zaferturan@nilufer.bel.tr').all()
    
    print("Response copied alanları güncelleniyor...")
    
    for user in users:
        # Bu kullanıcının tüm Response'larını al
        responses = session.query(Response).join(Request).filter(Request.user_id == user.id).all()
        
        if not responses:
            continue
            
        # Yaklaşık yarısını seç
        half_count = max(1, len(responses) // 2)
        selected_responses = random.sample(responses, half_count)
        
        # Seçilen Response'ların copied alanını True yap
        for response in selected_responses:
            response.copied = True
        
        print(f"{user.full_name}: {len(responses)} Response, {half_count} tanesi copied=True yapıldı")
    
    session.commit()
    print("Tüm güncellemeler tamamlandı!")
    session.close()

if __name__ == "__main__":
    update_copied()
