from fastapi import APIRouter, Depends

from app.api.dependencies import get_auth_service
from app.application.dto import LoginDTO, TokenResponseDTO
from app.domain.services import AuthService


router = APIRouter(prefix="/tokens", tags=["Inicio de sesión"])


@router.post(
    "",
    response_model=TokenResponseDTO,
    status_code=201,
)
def login(
    data: LoginDTO,
    service: AuthService = Depends(get_auth_service),
):

    token, user = service.login(data.usuario, data.password)

    return TokenResponseDTO(
        access_token=token,
        usuario=user.usuario,
        nombre=user.nombre,
        rol=user.rol,
    )
