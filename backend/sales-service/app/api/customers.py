from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user, get_customer_service
from app.application.dto import CreateCustomerDTO, CustomerPageDTO, CustomerResponseDTO, PatchCustomerDTO
from app.domain.models import TIPOS_DOCUMENTO, Customer
from app.domain.services import CustomerData, CustomerService
from app.infrastructure.security import TokenUser


router = APIRouter(prefix="/customers", tags=["Clientes"])


def to_response(customer: Customer) -> CustomerResponseDTO:
    return CustomerResponseDTO(
        id_cliente=customer.id,
        nombre=customer.nombre,
        tipo_documento=customer.tipo_documento,
        documento=customer.documento,
        telefono=customer.telefono,
        correo=customer.correo,
        direccion=customer.direccion,
        barrio=customer.barrio,
        ciudad=customer.ciudad,
        creado_en=customer.creado_en,
    )


@router.get(
    "",
    response_model=list[CustomerResponseDTO],
)
def search_customers(
    search: str = Query(default="", description="Nombre, documento, teléfono o id"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: TokenUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):

    return [to_response(c) for c in service.search_customers(search, limit, offset)]


@router.get(
    "/page",
    response_model=CustomerPageDTO,
)
def customers_page(
    search: str = "",
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: TokenUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):
    """Listado paginado con el total de resultados (para la tabla de clientes)."""

    return CustomerPageDTO(
        total=service.count_customers(search),
        clientes=[to_response(c) for c in service.search_customers(search, limit, offset)],
    )


@router.get(
    "/document-types",
    response_model=dict[str, str],
)
def document_types(user: TokenUser = Depends(get_current_user)):
    return TIPOS_DOCUMENTO


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

    return to_response(service.create_customer(CustomerData(**data.model_dump())))


@router.patch(
    "/{customer_id}",
    response_model=CustomerResponseDTO,
)
def update_customer(
    customer_id: int,
    data: PatchCustomerDTO,
    user: TokenUser = Depends(get_current_user),
    service: CustomerService = Depends(get_customer_service),
):

    return to_response(service.update_customer(customer_id, CustomerData(**data.model_dump(exclude_unset=True))))
