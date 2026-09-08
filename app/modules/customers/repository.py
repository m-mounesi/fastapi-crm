from core.exceptions import CustomerNotFoundException, PermissionDeniedException
from app.modules.customers.models import CustomerDB
from datetime import datetime, timezone


class CustomerRepository:
    def create(self, db, customer: CustomerDB):
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    def get_by_id(self, db, customer_id: int):
        return (
            db.query(CustomerDB)
            .filter(CustomerDB.id == customer_id, CustomerDB.deleted_at.is_(None))
            .first()
        )

    def get_all(self, db, user_id: int, is_admin: bool, skip: int = 0, limit: int = 10):
        query = db.query(CustomerDB).filter(CustomerDB.deleted_at.is_(None))

        if not is_admin:
            query = query.filter(CustomerDB.created_by == user_id)

        return query.offset(skip).limit(limit).all()

    def update(self, db, customer: CustomerDB):
        db.commit()
        db.refresh(customer)
        return customer

    # def get_trash(self, db, user_id: int, is_admin: bool):
    #     query = db.query(CustomerDB).filter(CustomerDB.deleted_at.is_not(None))

    #     if not is_admin:
    #         query = query.filter(CustomerDB.created_by == user_id)

    #     return query.all()

    def restore(self, db, customer_id: int, user_id, is_admin: bool):
        customer: CustomerDB = (
            db.query(CustomerDB).filter(CustomerDB.id == customer_id).first()
        )

        if not customer:
            raise CustomerNotFoundException("Customer not found")

        if not is_admin and customer.created_by != user_id:
            raise PermissionDeniedException("You cannot restore this customer.")

        customer.deleted_at = None
        db.commit()
        db.refresh(customer)

        return customer

    def delete(self, db, customer: CustomerDB):
        customer.deleted_at = datetime.now(timezone.utc)
        db.commit()
