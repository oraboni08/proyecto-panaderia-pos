from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import BusinessRuleError, ConflictError, NotFoundError


STATUS_BY_ERROR = {
    NotFoundError: 404,
    BusinessRuleError: 400,
    ConflictError: 409,
}


def register_error_handlers(app: FastAPI) -> None:
    """Traduce las excepciones del dominio a códigos HTTP."""

    for error_class, status_code in STATUS_BY_ERROR.items():

        def handler(request: Request, exc: Exception, status_code=status_code):
            return JSONResponse(status_code=status_code, content={"detail": str(exc)})

        app.add_exception_handler(error_class, handler)
