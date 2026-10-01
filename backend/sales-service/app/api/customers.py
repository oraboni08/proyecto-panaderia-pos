from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_customer_service
from app.application.dto import CreateCustomerDTO, CustomerResponseDTO
from app.domain.models import Customer
from app.domain.services import CustomerService
from app.infrastructure.security import TokenUser


router = APIRouter(prefix="/customers", tags=["Clientes"])


def to_response(customer: Customer) -> CustomerResponseDTO:
    return CustomerResponseDTO(id_cliente=customer.id, nombre=customer.nombre)


@router.get(
    "",
    response_model=list[CustomerResponseDTO],
)
def search_customers(
    search: str = "",
    limit: int = Query(default=20, ge=1, le=100),
    user: TokenUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):

    return [to_response(c) for c in service.search_customers(search, limit)]


@router.get(
    "/{customer_id}",
    response_model=CustomerResponseDTO,
)
def get_customer(
    customer_id: int,
    user: TokenUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):

    return to_response(service.get_customer(customer_id))


@router.post(
    "",
    response_model=CustomerResponseDTO,
    status_code=201,
)
def create_customer(
    data: CreateCustomerDTO,
    user: TokenUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):

    return to_response(service.create_customer(data.nombre))
