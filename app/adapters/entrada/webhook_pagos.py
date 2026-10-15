"""Endpoint que reciben las pasarelas cuando una transacción cambia de estado.

Cada pasarela manda un JSON distinto; aquí solo se traduce a ConfirmacionPago.
Las decisiones (aprobar, rechazar, emitir boletos) las toma el núcleo.
"""
from fastapi import APIRouter, HTTPException, Request

from app.core.domain.enums import MedioPago
from app.core.domain.models import ConfirmacionPago

router = APIRouter(prefix="/webhooks/pagos", tags=["Webhooks de pago"])


def _desde_paypal(p: dict) -> ConfirmacionPago:
    # {"orden_id": "...", "referencia": "PAYPAL-...", "status": "COMPLETED"}
    return ConfirmacionPago(p["orden_id"], MedioPago.PAYPAL, p["referencia"], p["status"] == "COMPLETED")


def _desde_wompi(p: dict) -> ConfirmacionPago:
    # {"data": {"transaction": {"reference": "<orden_id>", "id": "WOMPI-...", "status": "APPROVED"}}}
    t = p["data"]["transaction"]
    return ConfirmacionPago(t["reference"], MedioPago.WOMPI, t["id"], t["status"] == "APPROVED")


def _desde_pse(p: dict) -> ConfirmacionPago:
    # {"orden_id": "...", "cus": "PSE-...", "estado": "OK"}
    return ConfirmacionPago(p["orden_id"], MedioPago.PSE, p["cus"], p["estado"] == "OK")


MAPEADORES = {"paypal": _desde_paypal, "wompi": _desde_wompi, "pse": _desde_pse}


@router.post("/{pasarela}")
def recibir_notificacion(pasarela: str, payload: dict, request: Request):
    mapear = MAPEADORES.get(pasarela.lower())
    if mapear is None:
        raise HTTPException(404, f"Pasarela desconocida: {pasarela}")
    try:
        confirmacion = mapear(payload)
    except (KeyError, TypeError):
        raise HTTPException(400, "El cuerpo de la notificación no tiene el formato esperado")

    boletos = request.app.state.contenedor.confirmar_pago.confirmar_pago(confirmacion)
    return {
        "orden_id": confirmacion.orden_id,
        "aprobado": confirmacion.aprobado,
        "boletos": [
            {"id": b.id, "codigo_redencion": b.codigo_redencion, "firma_hash": b.firma_hash,
             "fecha_emision": b.fecha_emision.isoformat()}
            for b in boletos
        ],
    }
