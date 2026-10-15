import hashlib
import hmac
import io
import secrets
import string

import qrcode

from app.core.domain.models import Boleto, OrdenCompra
from app.core.ports.salida.servicios import GeneradorCredencialPort

ALFABETO = string.ascii_uppercase + string.digits


class Sha256CredencialAdapter(GeneradorCredencialPort):
    """Firma los boletos con HMAC-SHA256 y genera el QR en PNG."""

    def generar_codigo_redencion(self) -> str:
        return "".join(secrets.choice(ALFABETO) for _ in range(10))

    def calcular_firma(self, orden: OrdenCompra, codigo: str, clave_evento: str) -> str:
        # Solo datos que no cambian después de crear la orden
        datos = "|".join([
            orden.id,
            orden.cliente.id,
            orden.evento_id,
            ",".join(sorted(a.id for a in orden.asientos)),
            f"{orden.monto_total:.2f}",
            codigo,
        ])
        return hmac.new(clave_evento.encode(), datos.encode(), hashlib.sha256).hexdigest()

    def generar_qr(self, boleto: Boleto) -> bytes:
        contenido = f"{boleto.id}|{boleto.codigo_redencion}|{boleto.firma_hash}"
        buffer = io.BytesIO()
        qrcode.make(contenido).save(buffer, format="PNG")
        return buffer.getvalue()
