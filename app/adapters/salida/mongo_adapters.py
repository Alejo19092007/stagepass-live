from dataclasses import asdict
from datetime import datetime

from pymongo.collection import Collection

from app.core.domain.enums import EstadoAsiento, EstadoOrden, MedioPago
from app.core.domain.models import Asiento, Boleto, Cliente, OrdenCompra
from app.core.ports.salida.repositorios import BoletoRepositoryPort, OrdenRepositoryPort


class MongoOrdenAdapter(OrdenRepositoryPort):
    def __init__(self, coleccion: Collection):
        self.coleccion = coleccion

    def guardar(self, orden: OrdenCompra) -> None:
        self.coleccion.replace_one({"_id": orden.id}, self._a_documento(orden), upsert=True)

    def buscar_por_id(self, orden_id: str) -> OrdenCompra | None:
        doc = self.coleccion.find_one({"_id": orden_id})
        return self._a_dominio(doc) if doc else None

    def buscar_vencidas(self, ahora: datetime) -> list[OrdenCompra]:
        docs = self.coleccion.find({"estado": EstadoOrden.PENDIENTE_PAGO.value, "expira_en": {"$lte": ahora}})
        return [self._a_dominio(d) for d in docs]

    def contar_boletos(self, cliente_id: str, evento_id: str) -> int:
        resultado = list(self.coleccion.aggregate([
            {"$match": {
                "cliente.id": cliente_id,
                "evento_id": evento_id,
                "estado": {"$in": [EstadoOrden.PENDIENTE_PAGO.value, EstadoOrden.APROBADA.value]},
            }},
            {"$group": {"_id": None, "total": {"$sum": {"$size": "$asientos"}}}},
        ]))
        return resultado[0]["total"] if resultado else 0

    @staticmethod
    def _a_documento(o: OrdenCompra) -> dict:
        return {
            "_id": o.id,
            "cliente": asdict(o.cliente),
            "evento_id": o.evento_id,
            "asientos": [{**asdict(a), "estado": a.estado.value} for a in o.asientos],
            "medio_pago": o.medio_pago.value,
            "expira_en": o.expira_en,
            "tarifa_servicio": o.tarifa_servicio,
            "descuento": o.descuento,
            "monto_total": o.monto_total,
            "estado": o.estado.value,
            "referencia_pago": o.referencia_pago,
        }

    @staticmethod
    def _a_dominio(d: dict) -> OrdenCompra:
        return OrdenCompra(
            id=d["_id"],
            cliente=Cliente(**d["cliente"]),
            evento_id=d["evento_id"],
            asientos=[Asiento(a["id"], a["recinto_id"], a["codigo_ubicacion"], a["precio_base"],
                              EstadoAsiento(a["estado"])) for a in d["asientos"]],
            medio_pago=MedioPago(d["medio_pago"]),
            expira_en=d["expira_en"],
            tarifa_servicio=d["tarifa_servicio"],
            descuento=d["descuento"],
            monto_total=d["monto_total"],
            estado=EstadoOrden(d["estado"]),
            referencia_pago=d.get("referencia_pago"),
        )


class MongoBoletoAdapter(BoletoRepositoryPort):
    def __init__(self, coleccion: Collection):
        self.coleccion = coleccion

    def guardar(self, boleto: Boleto) -> None:
        doc = asdict(boleto)
        doc["_id"] = doc.pop("id")
        self.coleccion.replace_one({"_id": boleto.id}, doc, upsert=True)

    def buscar_por_orden(self, orden_id: str) -> list[Boleto]:
        return [Boleto(id=d["_id"], orden_id=d["orden_id"], codigo_redencion=d["codigo_redencion"],
                       firma_hash=d["firma_hash"], fecha_emision=d["fecha_emision"])
                for d in self.coleccion.find({"orden_id": orden_id})]
