-- ============================================================================
-- SISTEMA DE MONITOREO DE CRUCES FERROVIARIOS
-- Script Básico de Base de Datos PostgreSQL - Solo Estructura
-- ============================================================================

-- Crear la base de datos
CREATE DATABASE cruces_ferroviarios;

-- Conectar a la base de datos
\c cruces_ferroviarios;

-- ============================================================================
-- TABLAS PRINCIPALES
-- ============================================================================

-- 1. Cruce
CREATE TABLE cruce (
  id_cruce   SERIAL PRIMARY KEY,
  nombre     VARCHAR(255) NOT NULL,
  ubicacion  VARCHAR(255) NOT NULL,
  estado     VARCHAR(20) NOT NULL
             CHECK (estado IN ('ACTIVO','MANTENIMIENTO'))
);

-- 2. Sensor (1 por cruce)
CREATE TABLE sensor (
  id_sensor     SERIAL PRIMARY KEY,
  id_cruce      INTEGER NOT NULL
                REFERENCES cruce(id_cruce)
                UNIQUE,
  mac_address   VARCHAR(17) UNIQUE NOT NULL,
  installed_at  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Telemetría
CREATE TABLE telemetria (
  id_telemetria BIGSERIAL PRIMARY KEY,
  sensor_id     INTEGER NOT NULL
                REFERENCES sensor(id_sensor),
  ts            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  nivel_bateria DOUBLE PRECISION NOT NULL,
  voltaje       DOUBLE PRECISION NOT NULL,
  estado_barrera BOOLEAN NOT NULL,
  gabinete_abierto BOOLEAN NOT NULL
);

CREATE INDEX idx_telemetria_sensor_ts
  ON telemetria(sensor_id, ts DESC);

-- 4. Eventos de barrera
CREATE TABLE barrier_event (
  id_evento      BIGSERIAL PRIMARY KEY,
  sensor_id      INTEGER NOT NULL
                 REFERENCES sensor(id_sensor),
  telemetria_id  BIGINT   REFERENCES telemetria(id_telemetria),
  evento         VARCHAR(4) NOT NULL
                 CHECK (evento IN ('DOWN','UP')),
  ts_evento      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_event_sensor_ts
  ON barrier_event(sensor_id, ts_evento DESC);

-- 5. Alertas genéricas
CREATE TABLE api_alerta (
  id            SERIAL PRIMARY KEY,
  sensor_id     INTEGER REFERENCES sensor(id_sensor),
  telemetria_id BIGINT   REFERENCES telemetria(id_telemetria),
  type          VARCHAR(20) NOT NULL,
  description   TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved      BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_alerta_resolved ON api_alerta(resolved);

-- ============================================================================
-- FINALIZACIÓN
-- ============================================================================

-- Mostrar estructura creada
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

VACUUM ANALYZE; 