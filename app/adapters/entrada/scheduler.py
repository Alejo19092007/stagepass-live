import asyncio
import logging

from starlette.concurrency import run_in_threadpool

from app.core.ports.entrada.casos_uso import LiberarReservasUseCase

log = logging.getLogger("stagepass.scheduler")


class ExpiracionScheduler:
    """Revisa cada cierto tiempo si hay órdenes con el bloqueo de 10 minutos vencido."""

    def __init__(self, liberar_reservas: LiberarReservasUseCase, intervalo_segundos: int = 30):
        self.liberar_reservas = liberar_reservas
        self.intervalo = intervalo_segundos
        self._tarea: asyncio.Task | None = None

    async def _ciclo(self):
        while True:
            try:
                liberadas = await run_in_threadpool(self.liberar_reservas.liberar_expiradas)
                if liberadas:
                    log.info("Se liberaron %d orden(es) vencidas", liberadas)
            except Exception:
                log.exception("Error liberando reservas")
            await asyncio.sleep(self.intervalo)

    def iniciar(self):
        self._tarea = asyncio.create_task(self._ciclo())

    async def detener(self):
        if self._tarea:
            self._tarea.cancel()
