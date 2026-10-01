from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.domain.services import AuthService, UserService
from app.infrastructure.database import SessionLocal
from app.infrastructure.repositories import SQLAlchemyUserRepository
from app.infrastructure.security import (
    BcryptPasswordHasher,
    InvalidTokenError,
    JwtTokenProvider,
    TokenUser,
    decode_token,
)


bearer = HTTPBearer(auto_error=False)


def get_db():

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


def get_auth_service(
    db: Session = Depends(get_db),
) -> AuthService:

    return AuthService(
        SQLAlchemyUserRepository(db),
        BcryptPasswordHasher(),
        JwtTokenProvider(),
    )


def get_user_service(
    db: Session = Depends(get_db),
) -> UserService:

    return UserService(
        SQLAlchemyUserRepository(db),
        BcryptPasswordHasher(),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> TokenUser:

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return decode_token(credentials.credentials)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_admin(
    user: TokenUser = Depends(get_current_user),
) -> TokenUser:

    if user.rol != "admin":
        raise HTTPException(
            status_code=403,
            detail="Solo el administrador puede realizar esta acción",
        )

    return user
