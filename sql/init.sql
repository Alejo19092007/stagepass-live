-- Base de datos legacy de recintos (MySQL)
CREATE TABLE IF NOT EXISTS eventos (
    id            VARCHAR(36)  PRIMARY KEY,
    nombre        VARCHAR(120) NOT NULL,
    tipo          VARCHAR(20)  NOT NULL,
    recinto_id    VARCHAR(36)  NOT NULL,
    fecha_hora    DATETIME     NOT NULL,
    estado        VARCHAR(20)  NOT NULL,
    clave_secreta VARCHAR(64)  NOT NULL
);

CREATE TABLE IF NOT EXISTS asientos (
    id               VARCHAR(36)   PRIMARY KEY,
    recinto_id       VARCHAR(36)   NOT NULL,
    codigo_ubicacion VARCHAR(20)   NOT NULL,
    precio_base      DECIMAL(12,2) NOT NULL,
    estado           VARCHAR(20)   NOT NULL DEFAULT 'DISPONIBLE'
);

CREATE TABLE IF NOT EXISTS clientes (
    id              VARCHAR(36)  PRIMARY KEY,
    nombre_completo VARCHAR(120) NOT NULL,
    correo          VARCHAR(120) NOT NULL,
    telefono_movil  VARCHAR(20)  NOT NULL,
    nacionalidad    VARCHAR(40)  NOT NULL
);

INSERT INTO eventos VALUES
 ('EV-001', 'Festival Estéreo Bucaramanga', 'FESTIVAL', 'REC-01', '2026-12-05 18:00:00', 'PROGRAMADO', 'clave-festival-2026'),
 ('EV-002', 'Obra: La Casa de Bernarda Alba', 'TEATRO', 'REC-02', '2026-11-20 19:30:00', 'PROGRAMADO', 'clave-teatro-2026'),
 ('EV-003', 'Concierto Cancelado', 'CONCIERTO', 'REC-01', '2026-11-01 20:00:00', 'CANCELADO', 'clave-cancelado');

INSERT INTO asientos (id, recinto_id, codigo_ubicacion, precio_base) VALUES
 ('A-01', 'REC-01', 'VIP-A1', 350000), ('A-02', 'REC-01', 'VIP-A2', 350000),
 ('A-03', 'REC-01', 'VIP-A3', 350000), ('A-04', 'REC-01', 'VIP-A4', 350000),
 ('A-05', 'REC-01', 'General-01', 120000), ('A-06', 'REC-01', 'General-02', 120000),
 ('A-07', 'REC-01', 'General-03', 120000), ('A-08', 'REC-01', 'General-04', 120000),
 ('A-09', 'REC-01', 'General-05', 120000), ('A-10', 'REC-01', 'General-06', 120000),
 ('B-01', 'REC-02', 'Platea-01', 90000), ('B-02', 'REC-02', 'Platea-02', 90000),
 ('B-03', 'REC-02', 'Balcon-01', 60000);

INSERT INTO clientes VALUES
 ('CLI-001', 'Laura Gómez', 'laura@example.com', '+573001112233', 'Colombiana'),
 ('CLI-002', 'Andrés Pérez', 'andres@example.com', '+573004445566', 'Colombiana');
