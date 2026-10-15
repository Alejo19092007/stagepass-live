from enum import Enum


class TipoEvento(str, Enum):
    CONCIERTO = "CONCIERTO"
    TEATRO = "TEATRO"
    FESTIVAL = "FESTIVAL"


class EstadoEvento(str, Enum):
    PROGRAMADO = "PROGRAMADO"
    AGOTADO = "AGOTADO"
    CANCELADO = "CANCELADO"


class EstadoAsiento(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    BLOQUEADO = "BLOQUEADO"
    VENDIDO = "VENDIDO"


class EstadoOrden(str, Enum):
    PENDIENTE_PAGO = "PENDIENTE_PAGO"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    EXPIRADA = "EXPIRADA"


class MedioPago(str, Enum):
    PAYPAL = "PAYPAL"
    WOMPI = "WOMPI"
    PSE = "PSE"
