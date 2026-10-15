"""Adaptadores de notificación y facturación simulados (mocks)."""
import logging
import uuid

from app.core.domain.models import Boleto, Cliente, OrdenCompra
from app.core.ports.salida.servicios import FacturacionPort, NotificacionPort

log = logging.getLogger("stagepass.externos")


class WhatsAppAdapter(NotificacionPort):
    def __init__(self, token: str = "token-demo"):
        self.token = token
        self.enviados: list[tuple[str, int]] = []

    def enviar_boletos(self, cliente: Cliente, boletos: list[Boleto], qrs: list[bytes]) -> None:
        self.enviados.append((cliente.telefono_movil, len(boletos)))
        log.info("[WhatsApp] %d boleto(s) enviados a %s", len(boletos), cliente.telefono_movil)


class SendGridAdapter(NotificacionPort):
    def __init__(self, api_key: str = "key-demo"):
        self.api_key = api_key
        self.enviados: list[tuple[str, int]] = []

    def enviar_boletos(self, cliente: Cliente, boletos: list[Boleto], qrs: list[bytes]) -> None:
        self.enviados.append((cliente.correo, len(boletos)))
        log.info("[SendGrid] correo con %d boleto(s) enviado a %s", len(boletos), cliente.correo)


class DianFacturacionAdapter(FacturacionPort):
    def __init__(self):
        self.facturas: dict[str, str] = {}

    def emitir_factura(self, orden: OrdenCompra) -> str:
        numero = f"FE-{uuid.uuid4().hex[:8].upper()}"
        self.facturas[orden.id] = numero
        log.info("[DIAN] factura %s emitida por $%.2f", numero, orden.monto_total)
        return numero
