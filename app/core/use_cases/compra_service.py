from datetime import datetime
from typing import Callable

from app.core.domain.enums import MedioPago
from app.core.domain.exceptions import RecursoNoEncontradoException, ReglaNegocioException
from app.core.domain.models import OrdenCompra
from app.core.domain.politica_compra import PoliticaCompra
from app.core.ports.entrada.casos_uso import IniciarCompraUseCase
from app.core.ports.salida.repositorios import (
    ClienteRepositoryPort, OrdenRepositoryPort, RecintoRepositoryPort,
)
from app.core.ports.salida.servicios import PasarelaPagoPort


class CompraService(IniciarCompraUseCase):
    def __init__(self, recinto_repo: RecintoRepositoryPort, cliente_repo: ClienteRepositoryPort,
                 orden_repo: OrdenRepositoryPort, pasarelas: dict[MedioPago, PasarelaPagoPort],
                 politica: PoliticaCompra, reloj: Callable[[], datetime] = datetime.now):
        self.recinto_repo = recinto_repo
        self.cliente_repo = cliente_repo
        self.orden_repo = orden_repo
        self.pasarelas = pasarelas
        self.politica = politica
        self.reloj = reloj

    def iniciar_compra(self, cliente_id: str, evento_id: str, asiento_ids: list[str],
                       medio: MedioPago) -> OrdenCompra:
        evento = self.recinto_repo.buscar_evento(evento_id)
        if evento is None:
            raise RecursoNoEncontradoException(f"No existe el evento {evento_id}")
        if not evento.esta_disponible():
            raise ReglaNegocioException(f"El evento está {evento.estado.value}")

        cliente = self.cliente_repo.buscar_por_id(cliente_id)
        if cliente is None:
            raise RecursoNoEncontradoException(f"No existe el cliente {cliente_id}")

        ids = list(dict.fromkeys(asiento_ids))  # quita repetidos
        asientos = self.recinto_repo.buscar_asientos(ids)
        if len(asientos) != len(ids):
            raise RecursoNoEncontradoException("Alguno de los asientos no existe")
        if any(a.recinto_id != evento.recinto_id for a in asientos):
            raise ReglaNegocioException("Hay asientos que no pertenecen al recinto del evento")

        actuales = self.orden_repo.contar_boletos(cliente.id, evento.id)
        self.politica.validar_limite(actuales, len(asientos))

        pasarela = self.pasarelas.get(medio)
        if pasarela is None:
            raise ReglaNegocioException(f"Medio de pago no soportado: {medio}")

        orden = OrdenCompra.crear(cliente, evento.id, asientos, medio, self.reloj(), self.politica)
        orden.referencia_pago = pasarela.registrar_pago(orden)

        self.recinto_repo.actualizar_asientos(orden.asientos)
        self.orden_repo.guardar(orden)
        return orden
