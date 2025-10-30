import sys
sys.path.append('.')

from sqlalchemy.orm import Session
from sqlalchemy import func

from connection import SessionLocal
from models import User, Request as DBRequest, Response as DBResponse


def recompute_counters(db: Session) -> None:
    """
    Recompute and backfill per-user counters using existing data in the active DB.
    - answered_requests: count of distinct requests that have at least one copied response
    - total_requests: total number of responses created by the user (historical behavior)
    """

    users = db.query(User).all()
    for user in users:
        # Total produced responses (historical total_requests behavior)
        total_responses = (
            db.query(func.count(DBResponse.id))
            .join(DBRequest, DBRequest.id == DBResponse.request_id)
            .filter(DBRequest.user_id == user.id)
            .scalar()
        ) or 0

        # Distinct requests that were copied at least once
        answered = (
            db.query(DBRequest.id)
            .join(DBResponse, DBResponse.request_id == DBRequest.id)
            .filter(DBRequest.user_id == user.id, DBResponse.copied == True)
            .distinct()
            .count()
        ) or 0

        user.total_requests = int(total_responses)
        user.answered_requests = int(answered)

    db.commit()


def main() -> None:
    db = SessionLocal()
    try:
        recompute_counters(db)
        print("Counters recomputed and saved.")
    finally:
        db.close()


if __name__ == "__main__":
    main()


