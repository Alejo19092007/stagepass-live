from abc import ABC, abstractmethod

from app.core.domain.enums import MedioPago
from app.core.domain.models import Boleto, ConfirmacionPago, OrdenCompra


class IniciarCompraUseCase(ABC):
    @abstractmethod
    def iniciar_compra(self, cliente_id: str, evento_id: str, asiento_ids: list[str],
                       medio: MedioPago) -> OrdenCompra: ...


class ConfirmarPagoUseCase(ABC):
    @abstractmethod
    def confirmar_pago(self, confirmacion: ConfirmacionPago) -> list[Boleto]: ...


class LiberarReservasUseCase(ABC):
    @abstractmethod
    def liberar_expiradas(self) -> int: ...
