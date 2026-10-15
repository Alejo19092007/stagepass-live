"""Aquí se conectan los adaptadores con el núcleo (inyección de dependencias manual)."""
import os
from dataclasses import dataclass

from app.core.domain.enums import MedioPago
from app.core.domain.politica_compra import PoliticaCompra
from app.core.ports.entrada.casos_uso import (
    ConfirmarPagoUseCase, IniciarCompraUseCase, LiberarReservasUseCase,
)
from app.core.ports.salida.repositorios import (
    BoletoRepositoryPort, ClienteRepositoryPort, OrdenRepositoryPort, RecintoRepositoryPort,
)
from app.core.ports.salida.servicios import (
    FacturacionPort, GeneradorCredencialPort, NotificacionPort, PasarelaPagoPort,
)
from app.core.use_cases.compra_service import CompraService
from app.core.use_cases.confirmacion_pago_service import ConfirmacionPagoService
from app.core.use_cases.liberacion_reservas_service import LiberacionReservasService


@dataclass
class Contenedor:
    iniciar_compra: IniciarCompraUseCase
    confirmar_pago: ConfirmarPagoUseCase
    liberar_reservas: LiberarReservasUseCase


def armar_contenedor(recintos: RecintoRepositoryPort, clientes: ClienteRepositoryPort,
                     ordenes: OrdenRepositoryPort, boletos: BoletoRepositoryPort,
                     pasarelas: dict[MedioPago, PasarelaPagoPort], credenciales: GeneradorCredencialPort,
                     notificadores: list[NotificacionPort], facturacion: FacturacionPort,
                     reloj=None) -> Contenedor:
    extra = {"reloj": reloj} if reloj else {}
    politica = PoliticaCompra()
    return Contenedor(
        iniciar_compra=CompraService(recintos, clientes, ordenes, pasarelas, politica, **extra),
        confirmar_pago=ConfirmacionPagoService(ordenes, boletos, recintos, pasarelas, credenciales,
                                               notificadores, facturacion, **extra),
        liberar_reservas=LiberacionReservasService(ordenes, recintos, **extra),
    )


def contenedor_produccion() -> Contenedor:
    from pymongo import MongoClient

    from app.adapters.salida.credencial_adapter import Sha256CredencialAdapter
    from app.adapters.salida.mongo_adapters import MongoBoletoAdapter, MongoOrdenAdapter
    from app.adapters.salida.mysql_adapters import MySqlClienteAdapter, MySqlConexion, MySqlRecintoAdapter
    from app.adapters.salida.notificaciones import DianFacturacionAdapter, SendGridAdapter, WhatsAppAdapter
    from app.adapters.salida.pasarelas_pago import PayPalAdapter, PseAdapter, WompiAdapter

    mysql = MySqlConexion(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "stagepass"),
        password=os.getenv("MYSQL_PASSWORD", "stagepass"),
        database=os.getenv("MYSQL_DB", "stagepass_legacy"),
    )
    mongo = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017"))[os.getenv("MONGO_DB", "stagepass")]

    return armar_contenedor(
        recintos=MySqlRecintoAdapter(mysql),
        clientes=MySqlClienteAdapter(mysql),
        ordenes=MongoOrdenAdapter(mongo["ordenes"]),
        boletos=MongoBoletoAdapter(mongo["boletos"]),
        pasarelas={MedioPago.PAYPAL: PayPalAdapter(), MedioPago.WOMPI: WompiAdapter(), MedioPago.PSE: PseAdapter()},
        credenciales=Sha256CredencialAdapter(),
        notificadores=[WhatsAppAdapter(), SendGridAdapter()],
        facturacion=DianFacturacionAdapter(),
    )
