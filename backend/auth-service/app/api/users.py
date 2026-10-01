from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_user_service, require_admin
from app.application.dto import CreateUserDTO, PatchUserDTO, UserResponseDTO
from app.domain.models import User
from app.domain.services import UserService
from app.infrastructure.security import TokenUser


router = APIRouter(prefix="/users", tags=["Usuarios"])


def to_response(user: User) -> UserResponseDTO:
    # La contraseña cifrada nunca sale del servicio.
    return UserResponseDTO(
        id_usuario=user.id,
        nombre=user.nombre,
        usuario=user.usuario,
        rol=user.rol,
        activo=user.activo,
        creado_en=user.creado_en,
    )


@router.get(
    "/me",
    response_model=UserResponseDTO,
)
def get_me(
    user: TokenUser = Depends(get_current_user),
    service: UserService = Depends(get_user_service),
):

    return to_response(service.get_by_username(user.usuario))


@router.get(
    "",
    response_model=list[UserResponseDTO],
)
def list_users(
    user: TokenUser = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):

    return [to_response(u) for u in service.list_users()]


@router.post(
    "",
    response_model=UserResponseDTO,
    status_code=201,
)
def create_user(
    data: CreateUserDTO,
    user: TokenUser = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):

    created = service.create_user(
        nombre=data.nombre,
        usuario=data.usuario,
        password=data.password,
        rol=data.rol,
    )

    return to_response(created)


@router.patch(
    "/{user_id}",
    response_model=UserResponseDTO,
)
def update_user(
    user_id: int,
    data: PatchUserDTO,
    user: TokenUser = Depends(require_admin),
    service: UserService = Depends(get_user_service),
):

    updated = service.set_active(user_id, data.activo, user.usuario)

    return to_response(updated)
