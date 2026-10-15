class ReglaNegocioException(Exception):
    """Error base para cualquier regla de negocio que no se cumple."""


class RecursoNoEncontradoException(ReglaNegocioException):
    pass


class AsientoNoDisponibleException(ReglaNegocioException):
    pass


class LimiteBoletosExcedidoException(ReglaNegocioException):
    pass


class OrdenExpiradaException(ReglaNegocioException):
    pass


class PagoNoVerificadoException(ReglaNegocioException):
    pass
