"""Adaptadores en memoria para probar la API sin MySQL ni MongoDB (modo demo).

Cargan los mismos datos de ejemplo de sql/init.sql. Todo se pierde al cerrar la app.
"""
import copy
from datetime import datetime

from app.core.domain.enums import EstadoEvento, EstadoOrden, TipoEvento
from app.core.domain.models import Asiento, Boleto, Cliente, Evento, OrdenCompra
from app.core.ports.salida.repositorios import (
    BoletoRepositoryPort, ClienteRepositoryPort, OrdenRepositoryPort, RecintoRepositoryPort,
)


class MemoriaRecintoAdapter(RecintoRepositoryPort):
    def __init__(self):
        self.eventos = {e.id: e for e in [
            Evento("EV-001", "Festival Estéreo Bucaramanga", TipoEvento.FESTIVAL, "REC-01",
                   datetime(2026, 12, 5, 18), EstadoEvento.PROGRAMADO, "clave-festival-2026"),
            Evento("EV-002", "Obra: La Casa de Bernarda Alba", TipoEvento.TEATRO, "REC-02",
                   datetime(2026, 11, 20, 19, 30), EstadoEvento.PROGRAMADO, "clave-teatro-2026"),
            Evento("EV-003", "Concierto Cancelado", TipoEvento.CONCIERTO, "REC-01",
                   datetime(2026, 11, 1, 20), EstadoEvento.CANCELADO, "clave-cancelado"),
        ]}
        asientos = [Asiento(f"A-0{i}", "REC-01", f"VIP-A{i}", 350000) for i in range(1, 5)]
        asientos += [Asiento(f"A-{i:02d}", "REC-01", f"General-{i - 4:02d}", 120000) for i in range(5, 11)]
        asientos += [Asiento("B-01", "REC-02", "Platea-01", 90000), Asiento("B-02", "REC-02", "Platea-02", 90000),
                     Asiento("B-03", "REC-02", "Balcon-01", 60000)]
        self.asientos = {a.id: a for a in asientos}

    def buscar_evento(self, evento_id):
        return copy.deepcopy(self.eventos.get(evento_id))

    def buscar_asientos(self, asiento_ids):
        return [copy.deepcopy(self.asientos[i]) for i in asiento_ids if i in self.asientos]

    def actualizar_asientos(self, asientos):
        for a in asientos:
            self.asientos[a.id].estado = a.estado


class MemoriaClienteAdapter(ClienteRepositoryPort):
    def __init__(self):
        self.clientes = {
            "CLI-001": Cliente("CLI-001", "Laura Gómez", "laura@example.com", "+573001112233", "Colombiana"),
            "CLI-002": Cliente("CLI-002", "Andrés Pérez", "andres@example.com", "+573004445566", "Colombiana"),
        }

    def buscar_por_id(self, cliente_id):
        return self.clientes.get(cliente_id)


class MemoriaOrdenAdapter(OrdenRepositoryPort):
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


class MemoriaBoletoAdapter(BoletoRepositoryPort):
    def __init__(self):
        self.boletos: list[Boleto] = []

    def guardar(self, boleto):
        self.boletos.append(boleto)

    def buscar_por_orden(self, orden_id):
        return [b for b in self.boletos if b.orden_id == orden_id]
