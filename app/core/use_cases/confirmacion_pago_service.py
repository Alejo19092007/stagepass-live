import uuid
from datetime import datetime
from typing import Callable

from app.core.domain.enums import EstadoOrden, MedioPago
from app.core.domain.exceptions import (
    OrdenExpiradaException, PagoNoVerificadoException, RecursoNoEncontradoException,
    ReglaNegocioException,
)
from app.core.domain.models import Boleto, ConfirmacionPago, Evento, OrdenCompra
from app.core.ports.entrada.casos_uso import ConfirmarPagoUseCase
from app.core.ports.salida.repositorios import (
    BoletoRepositoryPort, OrdenRepositoryPort, RecintoRepositoryPort,
)
from app.core.ports.salida.servicios import (
    FacturacionPort, GeneradorCredencialPort, NotificacionPort, PasarelaPagoPort,
)


class ConfirmacionPagoService(ConfirmarPagoUseCase):
    def __init__(self, orden_repo: OrdenRepositoryPort, boleto_repo: BoletoRepositoryPort,
                 recinto_repo: RecintoRepositoryPort, pasarelas: dict[MedioPago, PasarelaPagoPort],
                 credenciales: GeneradorCredencialPort, notificadores: list[NotificacionPort],
                 facturacion: FacturacionPort, reloj: Callable[[], datetime] = datetime.now):
        self.orden_repo = orden_repo
        self.boleto_repo = boleto_repo
        self.recinto_repo = recinto_repo
        self.pasarelas = pasarelas
        self.credenciales = credenciales
        self.notificadores = notificadores
        self.facturacion = facturacion
        self.reloj = reloj

    def confirmar_pago(self, confirmacion: ConfirmacionPago) -> list[Boleto]:
        orden = self.orden_repo.buscar_por_id(confirmacion.orden_id)
        if orden is None:
            raise RecursoNoEncontradoException(f"No existe la orden {confirmacion.orden_id}")

        # Las pasarelas a veces reenvían la misma notificación: si ya se aprobó, devolvemos lo emitido.
        if orden.estado == EstadoOrden.APROBADA:
            return self.boleto_repo.buscar_por_orden(orden.id)

        if confirmacion.medio_pago != orden.medio_pago or confirmacion.referencia != orden.referencia_pago:
            raise PagoNoVerificadoException("La notificación no corresponde al pago registrado de la orden")

        if not confirmacion.aprobado:
            orden.rechazar()
            self._guardar(orden)
            return []

        pasarela = self.pasarelas.get(orden.medio_pago)
        if pasarela is None or not pasarela.verificar_pago(confirmacion):
            raise PagoNoVerificadoException("La pasarela no confirmó el pago")

        ahora = self.reloj()
        if orden.esta_expirada(ahora):
            orden.expirar()
            self._guardar(orden)
            raise OrdenExpiradaException("El pago llegó después de los 10 minutos de bloqueo")

        evento = self.recinto_repo.buscar_evento(orden.evento_id)
        if evento is None:
            raise ReglaNegocioException("El evento de la orden ya no existe")

        orden.aprobar(ahora)
        boletos = self._emitir_boletos(orden, evento, ahora)
        self._guardar(orden)
        for boleto in boletos:
            self.boleto_repo.guardar(boleto)

        self.facturacion.emitir_factura(orden)
        qrs = [self.credenciales.generar_qr(b) for b in boletos]
        for notificador in self.notificadores:
            notificador.enviar_boletos(orden.cliente, boletos, qrs)
        return boletos

    def _emitir_boletos(self, orden: OrdenCompra, evento: Evento, ahora: datetime) -> list[Boleto]:
        boletos = []
        for _ in orden.asientos:
            codigo = self.credenciales.generar_codigo_redencion()
            firma = self.credenciales.calcular_firma(orden, codigo, evento.clave_secreta)
            boletos.append(Boleto(str(uuid.uuid4()), orden.id, codigo, firma, ahora))
        return boletos

    def _guardar(self, orden: OrdenCompra) -> None:
        self.recinto_repo.actualizar_asientos(orden.asientos)
        self.orden_repo.guardar(orden)
