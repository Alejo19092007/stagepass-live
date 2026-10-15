"""Adaptadores de pago simulados (mocks).

Cada uno imita lo que haría el SDK real: registrar el cobro y devolver una referencia.
Para conectarlos de verdad solo se cambia el cuerpo de estas clases; el núcleo no se toca.
"""
import logging
import uuid

from app.core.domain.models import ConfirmacionPago, OrdenCompra
from app.core.ports.salida.servicios import PasarelaPagoPort

log = logging.getLogger("stagepass.pagos")


class _PasarelaSimulada(PasarelaPagoPort):
    prefijo = "SIM"

    def __init__(self):
        self.registrados: dict[str, float] = {}

    def registrar_pago(self, orden: OrdenCompra) -> str:
        referencia = f"{self.prefijo}-{uuid.uuid4().hex[:12].upper()}"
        self.registrados[referencia] = orden.monto_total
        log.info("[%s] cobro registrado %s por $%.2f (orden %s)", self.prefijo, referencia, orden.monto_total, orden.id)
        return referencia

    def verificar_pago(self, confirmacion: ConfirmacionPago) -> bool:
        # En un caso real aquí se consulta la API de la pasarela o se valida la firma del webhook.
        return confirmacion.referencia.startswith(self.prefijo + "-")


class PayPalAdapter(_PasarelaSimulada):
    prefijo = "PAYPAL"


class WompiAdapter(_PasarelaSimulada):
    prefijo = "WOMPI"


class PseAdapter(_PasarelaSimulada):
    prefijo = "PSE"
