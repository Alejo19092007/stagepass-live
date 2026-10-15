from .exceptions import LimiteBoletosExcedidoException


class PoliticaCompra:
    """Reglas de tarifas, descuentos y límites de StagePass Live."""

    LIMITE_BOLETOS_EVENTO = 6
    MINUTOS_BLOQUEO = 10

    def porcentaje_tarifa(self, cantidad: int) -> float:
        if cantidad <= 2:
            return 0.10
        if cantidad <= 5:
            return 0.08
        return 0.05

    def porcentaje_descuento(self, cantidad: int) -> float:
        if cantidad <= 2:
            return 0.0
        if cantidad <= 5:
            return 0.05
        return 0.10

    def validar_limite(self, actuales: int, nuevos: int) -> None:
        if actuales + nuevos > self.LIMITE_BOLETOS_EVENTO:
            raise LimiteBoletosExcedidoException(
                f"Un cliente no puede tener más de {self.LIMITE_BOLETOS_EVENTO} boletas para el mismo evento "
                f"(ya tiene {actuales}, intenta comprar {nuevos})"
            )
