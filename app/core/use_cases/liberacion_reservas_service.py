from datetime import datetime
from typing import Callable

from app.core.ports.entrada.casos_uso import LiberarReservasUseCase
from app.core.ports.salida.repositorios import OrdenRepositoryPort, RecintoRepositoryPort


class LiberacionReservasService(LiberarReservasUseCase):
    def __init__(self, orden_repo: OrdenRepositoryPort, recinto_repo: RecintoRepositoryPort,
                 reloj: Callable[[], datetime] = datetime.now):
        self.orden_repo = orden_repo
        self.recinto_repo = recinto_repo
        self.reloj = reloj

    def liberar_expiradas(self) -> int:
        vencidas = self.orden_repo.buscar_vencidas(self.reloj())
        for orden in vencidas:
            orden.expirar()
            self.recinto_repo.actualizar_asientos(orden.asientos)
            self.orden_repo.guardar(orden)
        return len(vencidas)
