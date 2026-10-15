import pytest

from app.adapters.salida.credencial_adapter import Sha256CredencialAdapter
from app.adapters.salida.notificaciones import DianFacturacionAdapter, SendGridAdapter, WhatsAppAdapter
from app.adapters.salida.pasarelas_pago import PayPalAdapter, PseAdapter, WompiAdapter
from app.config import armar_contenedor
from app.core.domain.enums import MedioPago
from tests.fakes import BoletosEnMemoria, ClientesEnMemoria, OrdenesEnMemoria, RecintosEnMemoria, Reloj


class Sistema:
    def __init__(self):
        self.recintos = RecintosEnMemoria()
        self.clientes = ClientesEnMemoria()
        self.ordenes = OrdenesEnMemoria()
        self.boletos = BoletosEnMemoria()
        self.reloj = Reloj()
        self.whatsapp = WhatsAppAdapter()
        self.correo = SendGridAdapter()
        self.dian = DianFacturacionAdapter()
        self.contenedor = armar_contenedor(
            self.recintos, self.clientes, self.ordenes, self.boletos,
            {MedioPago.PAYPAL: PayPalAdapter(), MedioPago.WOMPI: WompiAdapter(), MedioPago.PSE: PseAdapter()},
            Sha256CredencialAdapter(), [self.whatsapp, self.correo], self.dian, reloj=self.reloj,
        )


@pytest.fixture
def sistema():
    return Sistema()
