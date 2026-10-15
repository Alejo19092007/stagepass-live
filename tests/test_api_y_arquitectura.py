import ast
import pathlib

import mongomock
from fastapi.testclient import TestClient

from app.adapters.salida.mongo_adapters import MongoBoletoAdapter, MongoOrdenAdapter
from app.core.domain.enums import MedioPago
from app.main import create_app

NUCLEO = pathlib.Path(__file__).resolve().parents[1] / "app" / "core"
PERMITIDOS = {"abc", "dataclasses", "datetime", "enum", "typing", "uuid", "__future__"}


def test_el_nucleo_no_importa_nada_de_infraestructura():
    """Soberanía del dominio: el núcleo solo usa la librería estándar y su propio paquete."""
    for archivo in NUCLEO.rglob("*.py"):
        for nodo in ast.walk(ast.parse(archivo.read_text(encoding="utf-8"))):
            if isinstance(nodo, ast.Import):
                modulos = [n.name for n in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.level == 0:
                modulos = [nodo.module]
            else:
                continue
            for m in modulos:
                assert m.startswith("app.core") or m.split(".")[0] in PERMITIDOS, f"{archivo.name} importa {m}"


def cliente_api(sistema):
    return TestClient(create_app(sistema.contenedor, con_scheduler=False))


def test_flujo_http_compra_y_webhook_wompi(sistema):
    with cliente_api(sistema) as api:
        r = api.post("/compras", json={"cliente_id": "C1", "evento_id": "EV-1",
                                       "asiento_ids": ["A1", "A2", "A3", "A4", "A5", "A6"],
                                       "medio_pago": "WOMPI"})
        assert r.status_code == 201
        orden = r.json()
        assert orden["tarifa_servicio"] == 30_000 and orden["descuento"] == 60_000  # 5% y 10%

        r = api.post("/webhooks/pagos/wompi", json={"data": {"transaction": {
            "reference": orden["orden_id"], "id": orden["referencia_pago"], "status": "APPROVED"}}})
        assert r.status_code == 200
        assert len(r.json()["boletos"]) == 6


def test_errores_de_negocio_se_traducen_a_http(sistema):
    with cliente_api(sistema) as api:
        base = {"cliente_id": "C1", "evento_id": "EV-1", "medio_pago": "PSE"}
        assert api.post("/compras", json={**base, "asiento_ids": ["A1"]}).status_code == 201
        r = api.post("/compras", json={**base, "asiento_ids": ["A1"]})
        assert r.status_code == 409 and r.json()["error"] == "AsientoNoDisponibleException"
        assert api.post("/compras", json={**base, "evento_id": "NADA", "asiento_ids": ["A2"]}).status_code == 404
        assert api.post("/webhooks/pagos/bitcoin", json={}).status_code == 404


def test_adaptadores_mongo_guardan_y_reconstruyen_la_orden(sistema):
    db = mongomock.MongoClient().db
    sistema.contenedor.iniciar_compra.orden_repo = MongoOrdenAdapter(db.ordenes)
    ordenes = MongoOrdenAdapter(db.ordenes)
    boletos = MongoBoletoAdapter(db.boletos)

    orden = sistema.contenedor.iniciar_compra.iniciar_compra("C1", "EV-1", ["A1", "A2"], MedioPago.PAYPAL)
    leida = ordenes.buscar_por_id(orden.id)
    assert leida == orden
    assert ordenes.contar_boletos("C1", "EV-1") == 2
    assert ordenes.buscar_vencidas(orden.expira_en) == [orden]

    from app.core.domain.models import Boleto
    b = Boleto("B1", orden.id, "ABC123", "f" * 64, orden.expira_en)
    boletos.guardar(b)
    assert boletos.buscar_por_orden(orden.id) == [b]
