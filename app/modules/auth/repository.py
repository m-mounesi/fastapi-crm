from app.modules.auth.refresh_token import RefreshTokenDB


class RefreshTokenRepository:
    def create(self, db, token_obj: RefreshTokenDB):
        db.add(token_obj)
        db.commit()
        db.refresh(token_obj)
        return token_obj

    def get_by_token(self, db, token: str):
        return db.query(RefreshTokenDB).filter(RefreshTokenDB.token == token).first()

    def revoke(self, db, token: str):
        obj = self.get_by_token(db, token)
        if obj:
            obj.is_revoked = True
            db.commit()
        return obj
