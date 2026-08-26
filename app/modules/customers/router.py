from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_customer_service
from app.modules.users.models import UserDB
from schemas.schema import SuccessResponse
from app.modules.customers.service import CustomerService
from app.modules.customers.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
)

from security.dependencies import require_permission

router = APIRouter(prefix="/customers", tags=["customers"])


# CREATE Customer
@router.post("/", response_model=CustomerResponse)
def create_customer(
    data: CustomerCreate,
    service: CustomerService = Depends(get_customer_service),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_permission("customer.create")),
):
    return service.create_customer(db, data, current_user.user_id)


# GET ALL
@router.get("/", response_model=list[CustomerResponse])
def get_customers(
    skip: int = 0,
    limit: int = 10,
    service: CustomerService = Depends(get_customer_service),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_permission("customer.read")),
):
    return service.get_customers(db, current_user, skip, limit)


# GET BY ID
@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(
    customer_id: int,
    service: CustomerService = Depends(get_customer_service),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_permission("customer.read")),
):
    customer = service.get_customer(db, customer_id, current_user.user_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


# UPDATE
@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: int,
    data: CustomerUpdate,
    service: CustomerService = Depends(get_customer_service),
    db: Session = Depends(get_db),
    current_user: UserDB = Depends(require_permission("customer.update")),
):
    customer = service.update_customer(db, customer_id, data, current_user.user_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


# Delete
@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
    current_user: UserDB = Depends(require_permission("customer.delete")),
):
    result = service.delete_customer(db, customer_id, current_user.user_id)

    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")

    return SuccessResponse(
        message="Customer deleted successfully",
        data=f"Deleted Customer : {customer_id} ",
    )


# Restore
@router.post("/{customer_id}/restore")
def restore_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    service: CustomerService = Depends(get_customer_service),
    current_user: UserDB = Depends(require_permission("customer.restore")),
):
    customer = service.restore_customer(db, customer_id, current_user)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return SuccessResponse(
        message="Customer restored successfully", data=f"customer : {customer.name} "
    )
