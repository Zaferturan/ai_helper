#!/usr/bin/env python3
from connection import engine
from sqlalchemy.orm import Session
from models import User, Request, Response
from sqlalchemy import func

def check_answered_requests():
    session = Session(engine)
    users = session.query(User).all()
    
    print("Mevcut durum:")
    print("-" * 50)
    
    for user in users:
        # Toplam cevap sayısı
        total_responses = session.query(Response).join(Request).filter(Request.user_id == user.id).count()
        
        # Cevapladığı istek sayısı (unique request_id'ler)
        answered_requests = session.query(func.count(func.distinct(Request.id))).join(Response).filter(Request.user_id == user.id).scalar()
        
        print(f"{user.full_name}: {total_responses} toplam cevap, {answered_requests} cevapladığı istek")
    
    session.close()

if __name__ == "__main__":
    check_answered_requests()
