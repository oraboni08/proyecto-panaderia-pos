class DomainError(Exception):
    """Error base del dominio. La capa API lo traduce a un código HTTP."""


class NotFoundError(DomainError):
    """El recurso solicitado no existe (404)."""


class BusinessRuleError(DomainError):
    """Los datos violan una regla de negocio (400)."""


class ConflictError(DomainError):
    """El dato ya existe, por ejemplo un nombre repetido (409)."""
