import pymysql
from pymysql.cursors import DictCursor

from app.core.domain.enums import EstadoAsiento, EstadoEvento, TipoEvento
from app.core.domain.models import Asiento, Cliente, Evento
from app.core.ports.salida.repositorios import ClienteRepositoryPort, RecintoRepositoryPort


class MySqlConexion:
    def __init__(self, host: str, port: int, user: str, password: str, database: str):
        self.params = dict(host=host, port=port, user=user, password=password,
                           database=database, cursorclass=DictCursor, autocommit=True)

    def abrir(self):
        return pymysql.connect(**self.params)


class MySqlRecintoAdapter(RecintoRepositoryPort):
    def __init__(self, conexion: MySqlConexion):
        self.conexion = conexion

    def buscar_evento(self, evento_id: str) -> Evento | None:
        with self.conexion.abrir() as cn, cn.cursor() as cur:
            cur.execute("SELECT * FROM eventos WHERE id = %s", (evento_id,))
            fila = cur.fetchone()
        return self._a_evento(fila) if fila else None

    def buscar_asientos(self, asiento_ids: list[str]) -> list[Asiento]:
        if not asiento_ids:
            return []
        marcas = ", ".join(["%s"] * len(asiento_ids))
        with self.conexion.abrir() as cn, cn.cursor() as cur:
            cur.execute(f"SELECT * FROM asientos WHERE id IN ({marcas})", tuple(asiento_ids))
            filas = cur.fetchall()
        return [self._a_asiento(f) for f in filas]

    def actualizar_asientos(self, asientos: list[Asiento]) -> None:
        with self.conexion.abrir() as cn, cn.cursor() as cur:
            cur.executemany("UPDATE asientos SET estado = %s WHERE id = %s",
                            [(a.estado.value, a.id) for a in asientos])

    @staticmethod
    def _a_evento(f: dict) -> Evento:
        return Evento(f["id"], f["nombre"], TipoEvento(f["tipo"]), f["recinto_id"],
                      f["fecha_hora"], EstadoEvento(f["estado"]), f["clave_secreta"])

    @staticmethod
    def _a_asiento(f: dict) -> Asiento:
        return Asiento(f["id"], f["recinto_id"], f["codigo_ubicacion"],
                       float(f["precio_base"]), EstadoAsiento(f["estado"]))


class MySqlClienteAdapter(ClienteRepositoryPort):
    def __init__(self, conexion: MySqlConexion):
        self.conexion = conexion

    def buscar_por_id(self, cliente_id: str) -> Cliente | None:
        with self.conexion.abrir() as cn, cn.cursor() as cur:
            cur.execute("SELECT * FROM clientes WHERE id = %s", (cliente_id,))
            f = cur.fetchone()
        if not f:
            return None
        return Cliente(f["id"], f["nombre_completo"], f["correo"], f["telefono_movil"], f["nacionalidad"])
