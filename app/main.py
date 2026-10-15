import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.adapters.entrada import api_compras, webhook_pagos
from app.adapters.entrada.scheduler import ExpiracionScheduler
from app.config import Contenedor, contenedor_produccion
from app.core.domain.exceptions import (
    AsientoNoDisponibleException, LimiteBoletosExcedidoException, OrdenExpiradaException,
    PagoNoVerificadoException, RecursoNoEncontradoException, ReglaNegocioException,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

CODIGOS_HTTP = {
    RecursoNoEncontradoException: 404,
    AsientoNoDisponibleException: 409,
    LimiteBoletosExcedidoException: 409,
    OrdenExpiradaException: 410,
    PagoNoVerificadoException: 400,
}


def create_app(contenedor: Contenedor | None = None, con_scheduler: bool = True) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.contenedor = contenedor or contenedor_produccion()
        scheduler = ExpiracionScheduler(app.state.contenedor.liberar_reservas)
        if con_scheduler:
            scheduler.iniciar()
        yield
        await scheduler.detener()

    app = FastAPI(title="StagePass Live", lifespan=lifespan)
    app.include_router(api_compras.router)
    app.include_router(webhook_pagos.router)

    @app.exception_handler(ReglaNegocioException)
    async def manejar_regla(_: Request, exc: ReglaNegocioException):
        codigo = CODIGOS_HTTP.get(type(exc), 422)
        return JSONResponse(status_code=codigo, content={"error": type(exc).__name__, "detalle": str(exc)})

    return app


app = create_app()
