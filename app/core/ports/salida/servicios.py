from abc import ABC, abstractmethod

from app.core.domain.models import Boleto, Cliente, ConfirmacionPago, OrdenCompra


class PasarelaPagoPort(ABC):
    """Puerto común para PayPal, Wompi y PSE."""

    @abstractmethod
    def registrar_pago(self, orden: OrdenCompra) -> str:
        """Registra el cobro en la pasarela y devuelve la referencia del pago."""

    @abstractmethod
    def verificar_pago(self, confirmacion: ConfirmacionPago) -> bool:
        """Confirma con la pasarela que la notificación recibida es real."""


class GeneradorCredencialPort(ABC):
    @abstractmethod
    def generar_codigo_redencion(self) -> str: ...

    @abstractmethod
    def calcular_firma(self, orden: OrdenCompra, codigo: str, clave_evento: str) -> str: ...

    @abstractmethod
    def generar_qr(self, boleto: Boleto) -> bytes: ...


class NotificacionPort(ABC):
    @abstractmethod
    def enviar_boletos(self, cliente: Cliente, boletos: list[Boleto], qrs: list[bytes]) -> None: ...


class FacturacionPort(ABC):
    @abstractmethod
    def emitir_factura(self, orden: OrdenCompra) -> str: ...
