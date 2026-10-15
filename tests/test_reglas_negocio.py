from datetime import timedelta

import pytest

from app.core.domain.enums import EstadoAsiento, EstadoOrden, MedioPago
from app.core.domain.exceptions import (
    AsientoNoDisponibleException, LimiteBoletosExcedidoException, OrdenExpiradaException,
    PagoNoVerificadoException, RecursoNoEncontradoException, ReglaNegocioException,
)
from app.core.domain.models import ConfirmacionPago
from app.core.domain.politica_compra import PoliticaCompra


@pytest.mark.parametrize("cantidad, tarifa, descuento", [
    (1, 0.10, 0.0), (2, 0.10, 0.0),
    (3, 0.08, 0.05), (5, 0.08, 0.05),
    (6, 0.05, 0.10),
])
def test_tarifas_y_descuentos_por_volumen(cantidad, tarifa, descuento):
    p = PoliticaCompra()
    assert p.porcentaje_tarifa(cantidad) == tarifa
    assert p.porcentaje_descuento(cantidad) == descuento


def comprar(sistema, asientos, cliente="C1", medio=MedioPago.PAYPAL):
    return sistema.contenedor.iniciar_compra.iniciar_compra(cliente, "EV-1", asientos, medio)


def test_compra_bloquea_asientos_y_liquida_montos(sistema):
    orden = comprar(sistema, ["A1", "A2", "A3"])  # 3 x 100.000
    assert orden.tarifa_servicio == 24_000      # 8%
    assert orden.descuento == 15_000            # 5%
    assert orden.monto_total == 309_000
    assert orden.expira_en == sistema.reloj.ahora + timedelta(minutes=10)
    assert all(sistema.recintos.asientos[i].estado == EstadoAsiento.BLOQUEADO for i in ["A1", "A2", "A3"])


def test_no_se_puede_tomar_un_asiento_bloqueado(sistema):
    comprar(sistema, ["A1"])
    with pytest.raises(AsientoNoDisponibleException):
        comprar(sistema, ["A1", "A2"])
    assert sistema.recintos.asientos["A2"].estado == EstadoAsiento.DISPONIBLE


def test_limite_de_6_boletas_por_evento(sistema):
    comprar(sistema, ["A1", "A2", "A3", "A4"])
    comprar(sistema, ["A5", "A6"])
    with pytest.raises(LimiteBoletosExcedidoException):
        comprar(sistema, ["A7"])


def test_evento_cancelado_y_datos_invalidos(sistema):
    with pytest.raises(ReglaNegocioException):
        sistema.contenedor.iniciar_compra.iniciar_compra("C1", "EV-X", ["A1"], MedioPago.PSE)
    with pytest.raises(RecursoNoEncontradoException):
        comprar(sistema, ["A1"], cliente="NO-EXISTE")
    with pytest.raises(ReglaNegocioException):
        comprar(sistema, ["Z1"])  # asiento de otro recinto


def confirmar(sistema, orden, aprobado=True, referencia=None):
    c = ConfirmacionPago(orden.id, orden.medio_pago, referencia or orden.referencia_pago, aprobado)
    return sistema.contenedor.confirmar_pago.confirmar_pago(c)


def test_pago_aprobado_emite_boletos_firmados_y_notifica(sistema):
    orden = comprar(sistema, ["A1", "A2"])
    sistema.reloj.ahora += timedelta(minutes=5)
    boletos = confirmar(sistema, orden)

    assert len(boletos) == 2
    assert all(len(b.firma_hash) == 64 for b in boletos)            # sha256 en hex
    assert len({b.codigo_redencion for b in boletos}) == 2
    assert sistema.ordenes.ordenes[orden.id].estado == EstadoOrden.APROBADA
    assert sistema.recintos.asientos["A1"].estado == EstadoAsiento.VENDIDO
    assert orden.id in sistema.dian.facturas
    assert sistema.whatsapp.enviados and sistema.correo.enviados


def test_notificacion_repetida_no_duplica_boletos(sistema):
    orden = comprar(sistema, ["A1"])
    primera = confirmar(sistema, orden)
    segunda = confirmar(sistema, orden)
    assert [b.id for b in primera] == [b.id for b in segunda]
    assert len(sistema.boletos.boletos) == 1


def test_pago_rechazado_libera_asientos(sistema):
    orden = comprar(sistema, ["A1"])
    assert confirmar(sistema, orden, aprobado=False) == []
    assert sistema.ordenes.ordenes[orden.id].estado == EstadoOrden.RECHAZADA
    assert sistema.recintos.asientos["A1"].estado == EstadoAsiento.DISPONIBLE


def test_no_hay_boleto_si_el_pago_no_se_verifica(sistema):
    orden = comprar(sistema, ["A1"])
    with pytest.raises(PagoNoVerificadoException):
        confirmar(sistema, orden, referencia="REFERENCIA-FALSA")
    assert sistema.boletos.boletos == []


def test_pago_despues_de_10_minutos_no_se_acepta(sistema):
    orden = comprar(sistema, ["A1"])
    sistema.reloj.ahora += timedelta(minutes=10, seconds=1)
    with pytest.raises(OrdenExpiradaException):
        confirmar(sistema, orden)
    assert sistema.recintos.asientos["A1"].estado == EstadoAsiento.DISPONIBLE
    assert sistema.boletos.boletos == []


def test_liberacion_automatica_de_reservas_vencidas(sistema):
    vieja = comprar(sistema, ["A1", "A2"])
    sistema.reloj.ahora += timedelta(minutes=6)
    nueva = comprar(sistema, ["A3"])
    sistema.reloj.ahora += timedelta(minutes=5)   # la primera ya pasó 11 min, la segunda 5

    assert sistema.contenedor.liberar_reservas.liberar_expiradas() == 1
    assert sistema.ordenes.ordenes[vieja.id].estado == EstadoOrden.EXPIRADA
    assert sistema.ordenes.ordenes[nueva.id].estado == EstadoOrden.PENDIENTE_PAGO
    assert sistema.recintos.asientos["A1"].estado == EstadoAsiento.DISPONIBLE
    assert sistema.recintos.asientos["A3"].estado == EstadoAsiento.BLOQUEADO
