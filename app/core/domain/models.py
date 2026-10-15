from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .enums import EstadoAsiento, EstadoEvento, EstadoOrden, MedioPago, TipoEvento
from .exceptions import AsientoNoDisponibleException, OrdenExpiradaException, ReglaNegocioException
from .politica_compra import PoliticaCompra


@dataclass
class Cliente:
    id: str
    nombre_completo: str
    correo: str
    telefono_movil: str
    nacionalidad: str


@dataclass
class Evento:
    id: str
    nombre: str
    tipo: TipoEvento
    recinto_id: str
    fecha_hora: datetime
    estado: EstadoEvento
    clave_secreta: str

    def esta_disponible(self) -> bool:
        return self.estado == EstadoEvento.PROGRAMADO

    def marcar_agotado(self) -> None:
        self.estado = EstadoEvento.AGOTADO

    def cancelar(self) -> None:
        self.estado = EstadoEvento.CANCELADO


@dataclass
class Asiento:
    id: str
    recinto_id: str
    codigo_ubicacion: str
    precio_base: float
    estado: EstadoAsiento = EstadoAsiento.DISPONIBLE

    def esta_disponible(self) -> bool:
        return self.estado == EstadoAsiento.DISPONIBLE

    def bloquear(self) -> None:
        if not self.esta_disponible():
            raise AsientoNoDisponibleException(f"El asiento {self.codigo_ubicacion} no está disponible")
        self.estado = EstadoAsiento.BLOQUEADO

    def liberar(self) -> None:
        if self.estado == EstadoAsiento.BLOQUEADO:
            self.estado = EstadoAsiento.DISPONIBLE

    def vender(self) -> None:
        if self.estado != EstadoAsiento.BLOQUEADO:
            raise AsientoNoDisponibleException(f"El asiento {self.codigo_ubicacion} no estaba bloqueado")
        self.estado = EstadoAsiento.VENDIDO


@dataclass
class OrdenCompra:
    id: str
    cliente: Cliente
    evento_id: str
    asientos: list[Asiento]
    medio_pago: MedioPago
    expira_en: datetime
    tarifa_servicio: float = 0.0
    descuento: float = 0.0
    monto_total: float = 0.0
    estado: EstadoOrden = EstadoOrden.PENDIENTE_PAGO
    referencia_pago: str | None = None

    @classmethod
    def crear(cls, cliente: Cliente, evento_id: str, asientos: list[Asiento],
              medio_pago: MedioPago, ahora: datetime, politica: PoliticaCompra) -> OrdenCompra:
        if not asientos:
            raise ReglaNegocioException("Debe seleccionar al menos un asiento")
        for asiento in asientos:
            asiento.bloquear()
        orden = cls(
            id=str(uuid.uuid4()),
            cliente=cliente,
            evento_id=evento_id,
            asientos=asientos,
            medio_pago=medio_pago,
            expira_en=ahora + timedelta(minutes=politica.MINUTOS_BLOQUEO),
        )
        orden.liquidar(politica)
        return orden

    def subtotal(self) -> float:
        return sum(a.precio_base for a in self.asientos)

    def cantidad_boletos(self) -> int:
        return len(self.asientos)

    def liquidar(self, politica: PoliticaCompra) -> None:
        subtotal = self.subtotal()
        n = self.cantidad_boletos()
        self.tarifa_servicio = round(subtotal * politica.porcentaje_tarifa(n), 2)
        self.descuento = round(subtotal * politica.porcentaje_descuento(n), 2)
        self.monto_total = round(subtotal + self.tarifa_servicio - self.descuento, 2)

    def esta_expirada(self, ahora: datetime) -> bool:
        return ahora >= self.expira_en

    def _verificar_pendiente(self) -> None:
        if self.estado != EstadoOrden.PENDIENTE_PAGO:
            raise ReglaNegocioException(f"La orden ya está en estado {self.estado.value}")

    def aprobar(self, ahora: datetime) -> None:
        self._verificar_pendiente()
        if self.esta_expirada(ahora):
            raise OrdenExpiradaException("La orden expiró antes de confirmar el pago")
        for asiento in self.asientos:
            asiento.vender()
        self.estado = EstadoOrden.APROBADA

    def rechazar(self) -> None:
        self._verificar_pendiente()
        for asiento in self.asientos:
            asiento.liberar()
        self.estado = EstadoOrden.RECHAZADA

    def expirar(self) -> None:
        self._verificar_pendiente()
        for asiento in self.asientos:
            asiento.liberar()
        self.estado = EstadoOrden.EXPIRADA


@dataclass
class Boleto:
    id: str
    orden_id: str
    codigo_redencion: str
    firma_hash: str
    fecha_emision: datetime


@dataclass(frozen=True)
class ConfirmacionPago:
    """Lo que el dominio necesita saber de una notificación de pago, sin importar la pasarela."""
    orden_id: str
    medio_pago: MedioPago
    referencia: str
    aprobado: bool
