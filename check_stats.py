#!/usr/bin/env python3
from connection import engine
from sqlalchemy.orm import Session
from models import User, Request, Response

def check_stats():
    session = Session(engine)
    users = session.query(User).all()
    
    print("Güncel istatistikler:")
    print("-" * 50)
    
    for user in users:
        requests = session.query(Request).filter(Request.user_id == user.id).count()
        responses = session.query(Response).join(Request).filter(Request.user_id == user.id).count()
        print(f"{user.full_name}: {requests} istek, {responses} cevap")
    
    session.close()

if __name__ == "__main__":
    check_stats()
