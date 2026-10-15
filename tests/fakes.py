"""Adaptadores en memoria para probar el núcleo sin bases de datos."""
import copy
from datetime import datetime

from app.core.domain.enums import EstadoEvento, EstadoOrden, TipoEvento
from app.core.domain.models import Asiento, Boleto, Cliente, Evento, OrdenCompra
from app.core.ports.salida.repositorios import (
    BoletoRepositoryPort, ClienteRepositoryPort, OrdenRepositoryPort, RecintoRepositoryPort,
)


class RecintosEnMemoria(RecintoRepositoryPort):
    def __init__(self):
        self.eventos = {
            "EV-1": Evento("EV-1", "Festival", TipoEvento.FESTIVAL, "REC-1", datetime(2026, 12, 5, 18),
                           EstadoEvento.PROGRAMADO, "secreto"),
            "EV-X": Evento("EV-X", "Cancelado", TipoEvento.CONCIERTO, "REC-1", datetime(2026, 12, 1, 20),
                           EstadoEvento.CANCELADO, "secreto"),
        }
        self.asientos = {f"A{i}": Asiento(f"A{i}", "REC-1", f"GEN-{i}", 100_000.0) for i in range(1, 11)}
        self.asientos["Z1"] = Asiento("Z1", "REC-2", "OTRO-1", 50_000.0)

    def buscar_evento(self, evento_id):
        return copy.deepcopy(self.eventos.get(evento_id))

    def buscar_asientos(self, asiento_ids):
        return [copy.deepcopy(self.asientos[i]) for i in asiento_ids if i in self.asientos]

    def actualizar_asientos(self, asientos):
        for a in asientos:
            self.asientos[a.id].estado = a.estado


class ClientesEnMemoria(ClienteRepositoryPort):
    def __init__(self):
        self.clientes = {"C1": Cliente("C1", "Laura Gómez", "laura@x.com", "+573001112233", "Colombiana")}

    def buscar_por_id(self, cliente_id):
        return self.clientes.get(cliente_id)


class OrdenesEnMemoria(OrdenRepositoryPort):
    def __init__(self):
        self.ordenes: dict[str, OrdenCompra] = {}

    def guardar(self, orden):
        self.ordenes[orden.id] = copy.deepcopy(orden)

    def buscar_por_id(self, orden_id):
        return copy.deepcopy(self.ordenes.get(orden_id))

    def buscar_vencidas(self, ahora):
        return [copy.deepcopy(o) for o in self.ordenes.values()
                if o.estado == EstadoOrden.PENDIENTE_PAGO and o.esta_expirada(ahora)]

    def contar_boletos(self, cliente_id, evento_id):
        activos = (EstadoOrden.PENDIENTE_PAGO, EstadoOrden.APROBADA)
        return sum(o.cantidad_boletos() for o in self.ordenes.values()
                   if o.cliente.id == cliente_id and o.evento_id == evento_id and o.estado in activos)


class BoletosEnMemoria(BoletoRepositoryPort):
    def __init__(self):
        self.boletos: list[Boleto] = []

    def guardar(self, boleto):
        self.boletos.append(boleto)

    def buscar_por_orden(self, orden_id):
        return [b for b in self.boletos if b.orden_id == orden_id]


class Reloj:
    def __init__(self, inicio=datetime(2026, 10, 15, 10, 0)):
        self.ahora = inicio

    def __call__(self):
        return self.ahora
