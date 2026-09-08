from core.exceptions import CustomerNotFoundException, PermissionDeniedException
from app.modules.users.models import UserDB
from app.modules.customers.repository import CustomerRepository
from app.modules.customers.models import CustomerDB
from fastapi import HTTPException


class CustomerService:
    def __init__(self, repo: CustomerRepository):
        self.repo = repo

    # CREATE
    def create_customer(self, db, data, user_id: int):
        customer = CustomerDB(
            name=data.name,
            email=data.email,
            phone=data.phone,
            description=data.description,
            created_by=user_id,
        )

        return self.repo.create(db, customer)

    # GET ONE
    def get_customer(self, db, customer_id: int, user_id: int):
        customer = self.repo.get_by_id(db, customer_id)

        if not customer:
            raise CustomerNotFoundException("Customer not found by this id")

        if customer.created_by != user_id:
            raise PermissionDeniedException("Permission Denied!")

        return customer

    # GET ALL
    def get_customers(self, db, user: UserDB, skip: int = 0, limit: int = 10):
        return self.repo.get_all(
            db,
            user_id=user.user_id,
            is_admin=any(role.name == "admin" for role in user.roles),
            skip=skip,
            limit=limit,
        )

    # UPDATE
    def update_customer(self, db, customer_id: int, data, user_id: int):
        customer = self.repo.get_by_id(db, customer_id)

        if not customer:
            return None

        if customer.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this customer"
            )

        if data.name is not None:
            customer.name = data.name

        if data.email is not None:
            customer.email = data.email

        if data.phone is not None:
            customer.phone = data.phone

        if data.description is not None:
            customer.description = data.description

        return self.repo.update(db, customer)

    # DELETE
    def delete_customer(self, db, customer_id: int, user_id: int):
        customer = self.repo.get_by_id(db, customer_id)

        if not customer:
            return None

        if customer.created_by != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this customer"
            )

        self.repo.delete(db, customer)
        return True

    # RESTORE
    def restore_customer(self, db, customer_id, user: UserDB):
        is_admin = any(role.name == "admin" for role in user.roles)

        return self.repo.restore(db, customer_id, user.user_id, is_admin)
