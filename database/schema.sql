-- Esquema de base de datos para Hospital Dashboard AI
-- PostgreSQL compatible

-- Tabla de pacientes
CREATE TABLE IF NOT EXISTS pacientes (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(100),
    edad INTEGER CHECK (edad >= 0 AND edad <= 120),
    genero CHAR(1) CHECK (genero IN ('M', 'F', 'O')),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_ingreso VARCHAR(50) -- 'URGENCIA', 'CONSULTA_EXTERNA', 'CIRUGIA_PROGRAMADA'
);

-- Tabla de urgencias
CREATE TABLE IF NOT EXISTS urgencias (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER REFERENCES pacientes(id),
    fecha_entrada TIMESTAMP NOT NULL,
    fecha_atencion_medica TIMESTAMP,
    fecha_alta TIMESTAMP,
    triaje_nivel INTEGER CHECK (triaje_nivel BETWEEN 1 AND 5), -- 1: Crítico, 5: No urgente
    motivo VARCHAR(200),
    diagnostico VARCHAR(300),
    destino VARCHAR(50), -- 'ALTA', 'INGRESO', 'FALLECIMIENTO', 'FUGA'
    box INTEGER,
    tiempo_espera_minutos INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (fecha_atencion_medica - fecha_entrada))/60
    ) STORED
);

-- Tabla de quirófanos
CREATE TABLE IF NOT EXISTS quirofanos (
    id SERIAL PRIMARY KEY,
    numero VARCHAR(10) NOT NULL,
    especialidad VARCHAR(50),
    estado VARCHAR(20) DEFAULT 'DISPONIBLE' -- 'OCUPADO', 'DISPONIBLE', 'LIMPIEZA', 'MANTENIMIENTO'
);

-- Tabla de cirugías
CREATE TABLE IF NOT EXISTS cirugias (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER REFERENCES pacientes(id),
    quirofano_id INTEGER REFERENCES quirofanos(id),
    fecha_programada DATE,
    hora_inicio_programada TIME,
    hora_inicio_real TIME,
    hora_fin TIME,
    tipo_cirugia VARCHAR(100),
    cirujano VARCHAR(100),
    duracion_minutos INTEGER GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (hora_fin - hora_inicio_real))/60
    ) STORED,
    estado VARCHAR(30), -- 'COMPLETADA', 'CANCELADA', 'EN_CURSO', 'PROGRAMADA'
    motivo_cancelacion VARCHAR(200)
);

-- Tabla de consultas externas
CREATE TABLE IF NOT EXISTS consultas_externas (
    id SERIAL PRIMARY KEY,
    paciente_id INTEGER REFERENCES pacientes(id),
    especialidad VARCHAR(50) NOT NULL,
    medico VARCHAR(100),
    fecha_cita TIMESTAMP NOT NULL,
    fecha_atencion TIMESTAMP,
    estado VARCHAR(30), -- 'ATENDIDA', 'NO_SHOW', 'CANCELADA', 'PENDIENTE'
    tipo VARCHAR(30), -- 'PRIMERA_VISITA', 'REVISIT', 'CONTROL'
    tiempo_espera_dias INTEGER
);

-- Tabla de ocupación de camas
CREATE TABLE IF NOT EXISTS camas (
    id SERIAL PRIMARY KEY,
    numero VARCHAR(20) NOT NULL,
    servicio VARCHAR(50) NOT NULL, -- 'UC', 'UCI', 'MEDICINA', 'CIRUGIA', 'PEDIATRIA'
    estado VARCHAR(20) DEFAULT 'LIBRE', -- 'OCUPADA', 'LIBRE', 'LIMPIEZA'
    paciente_id INTEGER REFERENCES pacientes(id),
    fecha_ocupacion TIMESTAMP,
    fecha_liberacion TIMESTAMP
);

-- Índices para rendimiento
CREATE INDEX idx_urgencias_fecha ON urgencias(fecha_entrada);
CREATE INDEX idx_cirugias_fecha ON cirugias(fecha_programada);
CREATE INDEX idx_consultas_fecha ON consultas_externas(fecha_cita);
CREATE INDEX idx_camas_servicio ON camas(servicio);
