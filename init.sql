-- 1. Tabla para E-commerce (El catálogo que verá el cliente)
CREATE TABLE IF NOT EXISTS catalogo_servicios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL,
    tiempo_m1 FLOAT NOT NULL, 
    tiempo_m2 FLOAT NOT NULL  
);

-- 2. Tabla para Investigación de Operaciones (El Jobshop)
CREATE TABLE IF NOT EXISTS ordenes_trabajo (
    id_orden INT AUTO_INCREMENT PRIMARY KEY,
    servicio_id INT,
    cliente_nombre VARCHAR(100),
    fecha_entrega_minutos FLOAT NOT NULL, 
    estado ENUM('Pendiente', 'En Taller', 'En Tránsito', 'Entregado') DEFAULT 'Pendiente',
    orden_produccion INT NULL, 
    token_verificacion VARCHAR(6) NULL, 
    FOREIGN KEY (servicio_id) REFERENCES catalogo_servicios(id)
);

-- 3. Tabla para Sistemas Distribuidos (Las alertas Edge-to-Cloud)
CREATE TABLE IF NOT EXISTS kioscos (
    id_kiosco INT AUTO_INCREMENT PRIMARY KEY,
    ubicacion VARCHAR(100) NOT NULL,
    nivel_forjas INT DEFAULT 100, 
    efectivo_acumulado DECIMAL(10, 2) DEFAULT 0.00,
    estado ENUM('Operativo', 'Alerta', 'Mantenimiento') DEFAULT 'Operativo'
);

-- Insertar un servicio de prueba para arrancar
INSERT INTO catalogo_servicios (nombre, descripcion, precio, tiempo_m1, tiempo_m2) 
VALUES ('Duplicado Alta Seguridad', 'Llave con corte láser', 150.00, 5.0, 3.0);