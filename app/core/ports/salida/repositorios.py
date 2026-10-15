from abc import ABC, abstractmethod
from datetime import datetime

from app.core.domain.models import Asiento, Boleto, Cliente, Evento, OrdenCompra


class RecintoRepositoryPort(ABC):
    @abstractmethod
    def buscar_evento(self, evento_id: str) -> Evento | None: ...

    @abstractmethod
    def buscar_asientos(self, asiento_ids: list[str]) -> list[Asiento]: ...

    @abstractmethod
    def actualizar_asientos(self, asientos: list[Asiento]) -> None: ...


class ClienteRepositoryPort(ABC):
    @abstractmethod
    def buscar_por_id(self, cliente_id: str) -> Cliente | None: ...


class OrdenRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, orden: OrdenCompra) -> None: ...

    @abstractmethod
    def buscar_por_id(self, orden_id: str) -> OrdenCompra | None: ...

    @abstractmethod
    def buscar_vencidas(self, ahora: datetime) -> list[OrdenCompra]: ...

    @abstractmethod
    def contar_boletos(self, cliente_id: str, evento_id: str) -> int:
        """Boletos que el cliente ya tiene (o tiene apartados) para el evento."""


class BoletoRepositoryPort(ABC):
    @abstractmethod
    def guardar(self, boleto: Boleto) -> None: ...

    @abstractmethod
    def buscar_por_orden(self, orden_id: str) -> list[Boleto]: ...
