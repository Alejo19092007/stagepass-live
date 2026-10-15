from datetime import datetime

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.domain.enums import MedioPago
from app.core.domain.models import OrdenCompra

router = APIRouter(prefix="/compras", tags=["Compras"])


class CompraRequest(BaseModel):
    cliente_id: str
    evento_id: str
    asiento_ids: list[str] = Field(min_length=1)
    medio_pago: MedioPago


class OrdenResponse(BaseModel):
    orden_id: str
    estado: str
    asientos: list[str]
    subtotal: float
    tarifa_servicio: float
    descuento: float
    monto_total: float
    expira_en: datetime
    medio_pago: str
    referencia_pago: str | None

    @classmethod
    def desde_dominio(cls, o: OrdenCompra) -> "OrdenResponse":
        return cls(orden_id=o.id, estado=o.estado.value, asientos=[a.codigo_ubicacion for a in o.asientos],
                   subtotal=o.subtotal(), tarifa_servicio=o.tarifa_servicio, descuento=o.descuento,
                   monto_total=o.monto_total, expira_en=o.expira_en, medio_pago=o.medio_pago.value,
                   referencia_pago=o.referencia_pago)


@router.post("", response_model=OrdenResponse, status_code=201)
def iniciar_compra(req: CompraRequest, request: Request):
    caso_uso = request.app.state.contenedor.iniciar_compra
    orden = caso_uso.iniciar_compra(req.cliente_id, req.evento_id, req.asiento_ids, req.medio_pago)
    return OrdenResponse.desde_dominio(orden)
