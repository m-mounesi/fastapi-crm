from sqlalchemy.orm import Session
from app.modules.users.models import UserDB


class UserRepository:
    def create_user(self, db: Session, user_data):
        user = UserDB(
            username=user_data["username"],
            hashed_password=user_data["password"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def get_user(self, db: Session, username: str):
        user = db.query(UserDB).filter(UserDB.username == username).first()
        return user

    def get_by_id(self, db: Session, user_id: int):
        return db.query(UserDB).filter(UserDB.user_id == user_id).first()
