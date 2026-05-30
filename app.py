from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
# Inicializamos el servidor Flask
app = Flask(__name__)
# Llave secreta para encriptar las cookies de sesión
app.secret_key = 'erp_seguridad_b2_c1_super_secreta'

# Configuramos la conexión a tu base de datos Docker
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://isai_admin:TU_CONTRASEÑA@mysql-isai.alwaysdata.net/isai_cerrajeria_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Vinculamos la base de datos al servidor
db = SQLAlchemy(app)

# ==========================================
# MODELOS DE BASE DE DATOS (Mapeo)
# ==========================================

class CatalogoServicios(db.Model):
    __tablename__ = 'catalogo_servicios'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    precio = db.Column(db.Float)
    tiempo_m1 = db.Column(db.Float)
    tiempo_m2 = db.Column(db.Float)

class OrdenTrabajo(db.Model):
    __tablename__ = 'ordenes_trabajo'
    id_orden = db.Column(db.Integer, primary_key=True)
    servicio_id = db.Column(db.Integer)
    cliente_nombre = db.Column(db.String(100))
    fecha_entrega_minutos = db.Column(db.Float)
    estado = db.Column(db.String(20), default='Pendiente')
    orden_produccion = db.Column(db.Integer, nullable=True)
    estatus_pago = db.Column(db.String(20), default='Aprobado') 

class Kiosco(db.Model):
    __tablename__ = 'kioscos'
    id = db.Column(db.Integer, primary_key=True)
    ubicacion = db.Column(db.String(100))
    estado = db.Column(db.String(50), default='Operativo')
    efectivo_acumulado = db.Column(db.Float, default=0.0) # <--- NUEVA COLUMNA

class InventarioKiosco(db.Model):
    __tablename__ = 'inventario_kioscos'
    id = db.Column(db.Integer, primary_key=True)
    kiosco_id = db.Column(db.Integer)
    modelo_forja = db.Column(db.String(20))
    cantidad = db.Column(db.Integer)
    precio_unitario = db.Column(db.Float) # <--- NUEVA COLUMNA

# ==========================================
# RUTAS DEL SISTEMA
# ==========================================

# --- RUTAS DE PANTALLAS (FRONTEND) ---

# 1. La Tienda Pública (E-commerce)
@app.route('/')
def tienda_publica():
    return render_template('tienda.html')

# --- RUTAS DE SEGURIDAD Y CONTROL DE ACCESO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        usuario = request.form['usuario']
        password = request.form['password']
        
        # Validación de credenciales
        if usuario == 'admin' and password == 'admin123':
            session['logeado'] = True
            session['usuario'] = usuario
            return redirect(url_for('panel_admin'))
        else:
            error = 'Credenciales inválidas. Acceso denegado.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    # Destruir la sesión (quitar el gafete VIP)
    session.pop('logeado', None)
    session.pop('usuario', None)
    return redirect(url_for('login'))

@app.route('/admin-panel')
def panel_admin():
    # El Cadenero: Si no tienes el gafete 'logeado', te mando al login
    if not session.get('logeado'):
        return redirect(url_for('login'))
    
    # Si pasaste la validación, te muestro el dashboard
    return render_template('admin.html')

# --- HERRAMIENTA INTERNA: MOTOR DE OPTIMIZACIÓN ---
def aplicar_algoritmo_johnson():
    """Esta función corre en segundo plano y no depende de internet"""
    # Traer pedidos "Pendientes"
    pedidos = db.session.query(OrdenTrabajo, CatalogoServicios).join(
        CatalogoServicios, OrdenTrabajo.servicio_id == CatalogoServicios.id
    ).filter(OrdenTrabajo.estado == 'Pendiente').all()

    if not pedidos:
        return None

    # Preparar los datos
    trabajos = []
    for orden, servicio in pedidos:
        trabajos.append({
            'id_orden': orden.id_orden,
            't1': servicio.tiempo_m1,
            't2': servicio.tiempo_m2
        })

    # Lógica del Algoritmo de Johnson
    secuencia = [None] * len(trabajos)
    inicio = 0
    fin = len(trabajos) - 1
    trabajos_pendientes = trabajos.copy()

    while trabajos_pendientes:
        min_t = float('inf')
        trabajo_min = None
        maquina_min = 0

        for t in trabajos_pendientes:
            if t['t1'] < min_t:
                min_t = t['t1']
                trabajo_min = t
                maquina_min = 1
            if t['t2'] < min_t:
                min_t = t['t2']
                trabajo_min = t
                maquina_min = 2

        if maquina_min == 1:
            secuencia[inicio] = trabajo_min['id_orden']
            inicio += 1
        else:
            secuencia[fin] = trabajo_min['id_orden']
            fin -= 1
        
        trabajos_pendientes.remove(trabajo_min)

    # Guardar secuencia en MySQL
    orden_actual = 1
    for id_orden in secuencia:
        orden_db = OrdenTrabajo.query.get(id_orden)
        orden_db.orden_produccion = orden_actual
        orden_db.estado = 'En Taller' 
        orden_actual += 1
    
    db.session.commit()
    return secuencia


# 2. Ruta para el E-commerce (AHORA INTELIGENTE)
@app.route('/api/pedidos/nuevo', methods=['POST'])
def crear_pedido():
    try:
        datos = request.get_json()
        metodo_pago = datos.get('estatus_pago', 'Aprobado')
        
        # 1. Guardar el nuevo pedido
        nuevo_pedido = OrdenTrabajo(
            servicio_id=datos['servicio_id'],
            cliente_nombre=datos['cliente_nombre'],
            fecha_entrega_minutos=datos['fecha_entrega_minutos'],
            estatus_pago=metodo_pago # Guardamos el estatus real
        )
        db.session.add(nuevo_pedido)
        db.session.commit()
        
        # 2. Lógica Blindada: Solo optimizar si el pago pasó
        if metodo_pago == 'Declinado':
            return jsonify({
                "estado": "Error", 
                "mensaje": f"Pago declinado para {datos['cliente_nombre']}. El taller NO procesará este pedido."
            })
            
        # 3. Si el pago es Aprobado, optimizar taller
        secuencia = aplicar_algoritmo_johnson()
        
        return jsonify({
            "estado": "Éxito", 
            "mensaje": f"Pedido de {datos['cliente_nombre']} en producción. Taller auto-optimizado."
        })
        
    except Exception as e:
        return jsonify({"estado": "Error", "mensaje": str(e)})
    
# 4. Ruta para Sistemas Distribuidos (Alertas IoT y Flujo Financiero)
@app.route('/api/kioscos/alerta', methods=['POST'])
def recibir_alerta_kiosco():
    try:
        datos = request.get_json()
        k_id = datos['id_kiosco']
        forja = datos['modelo_forja']
        llaves_vendidas = datos['cantidad_vendida']

        # 🔒 CANDADO PESIMISTA
        item_inventario = InventarioKiosco.query.filter_by(
            kiosco_id=k_id, 
            modelo_forja=forja
        ).with_for_update().first()

        if not item_inventario:
            return jsonify({"estado": "Error", "mensaje": "Inventario no encontrado para esa forja."})

        # 🛡️ REGLA DE NEGOCIO: Validación de Stock (Evita números negativos)
        if llaves_vendidas > item_inventario.cantidad:
            db.session.rollback() # Soltamos el candado de la base de datos
            return jsonify({
                "estado": "Error", 
                "mensaje": f"Stock insuficiente. Solo quedan {item_inventario.cantidad} unidades de {forja}."
            })

        # --- LÓGICA FINANCIERA DINÁMICA ---
        ingreso_venta = llaves_vendidas * item_inventario.precio_unitario
        item_inventario.cantidad -= llaves_vendidas # Resta segura

        # Actualizamos el Kiosco
        kiosco_db = Kiosco.query.get(k_id)
        mensaje_extra = "" # Inicializamos la variable correctamente

        if kiosco_db:
            kiosco_db.efectivo_acumulado += ingreso_venta

            # EVALUACIÓN DE ESTADOS (Priorizamos la seguridad del dinero)
            if kiosco_db.efectivo_acumulado >= 3000:
                mensaje_extra = " ¡Bóveda Saturada! Requiere recolección."
                kiosco_db.estado = 'Saturado (Efectivo)'
            elif item_inventario.cantidad <= 10:
                mensaje_extra = f" ¡ALERTA! Reabastecer forja {forja}."
                kiosco_db.estado = 'Requiere Mantenimiento'
            else:
                kiosco_db.estado = 'Operativo'

        # 🔓 SE LIBERA EL CANDADO
        db.session.commit()

        return jsonify({
            "estado": "Éxito", 
            "inventario_restante": item_inventario.cantidad,
            "mensaje": f"Venta exitosa: ${ingreso_venta} MXN. Restan {item_inventario.cantidad}.{mensaje_extra}"
        })

    except Exception as e:
        db.session.rollback() 
        return jsonify({"estado": "Error", "mensaje": str(e)})
    
# 6--- RUTA DE INTELIGENCIA DE NEGOCIOS (BUSINESS INTELLIGENCE) ---
@app.route('/api/kioscos/estado', methods=['GET'])
def obtener_estado_kioscos():
    try:
        kioscos_db = Kiosco.query.all() 
        
        lista_kioscos = []
        for k in kioscos_db:
            lista_kioscos.append({
                "id": k.id,
                "ubicacion": k.ubicacion,
                "estado": k.estado,
                "efectivo_acumulado": k.efectivo_acumulado # <--- ¡ESTA ES LA LÍNEA MÁGICA QUE FALTABA!
            })
            
        return jsonify({"estado": "Éxito", "kioscos": lista_kioscos})
    except Exception as e:
        return jsonify({"estado": "Error", "mensaje": str(e)})
    
# 7. Ruta para el Cierre de Producción (Investigación de Operaciones)
@app.route('/api/taller/cerrar-lote', methods=['POST'])
def cerrar_lote():
    try:
        # Buscar todos los pedidos que actualmente están 'En Taller'
        pedidos_en_taller = OrdenTrabajo.query.filter_by(estado='En Taller').all()
        
        if not pedidos_en_taller:
            return jsonify({"estado": "Info", "mensaje": "Las máquinas están libres. No hay trabajos pendientes."})
        
        count = 0
        for pedido in pedidos_en_taller:
            pedido.estado = 'Terminado'
            pedido.orden_produccion = None # Limpiamos el número de secuencia
            count += 1
        
        db.session.commit()
        
        return jsonify({
            "estado": "Éxito", 
            "mensaje": f"¡Lote finalizado! Se marcaron {count} trabajos como 'Terminados'. Taller listo para el siguiente turno."
        })
    except Exception as e:
        return jsonify({"estado": "Error", "mensaje": str(e)})
    

@app.route('/api/kioscos/recolectar/<int:id_kiosco>', methods=['POST'])
def recolectar_efectivo(id_kiosco):
    try:
        kiosco = Kiosco.query.get(id_kiosco)
        if not kiosco:
            return jsonify({"estado": "Error", "mensaje": "Kiosco no encontrado."})
            
        # Simulación de recolección física
        kiosco.efectivo_acumulado = 0.0
        kiosco.estado = 'Operativo'
        db.session.commit()
        
        return jsonify({"estado": "Éxito", "mensaje": f"Efectivo recolectado en {kiosco.ubicacion}. Nodo operativo."})
    except Exception as e:
        return jsonify({"estado": "Error", "mensaje": str(e)})
    
# 8. Ruta para Reabastecimiento de Inventario (Logística)
@app.route('/api/kioscos/reabastecer/<int:id_kiosco>', methods=['POST'])
def reabastecer_inventario(id_kiosco):
    try:
        kiosco = Kiosco.query.get(id_kiosco)
        if not kiosco:
            return jsonify({"estado": "Error", "mensaje": "Kiosco no encontrado."})

        # Buscamos todas las forjas de este kiosco y las rellenamos a 50
        inventarios = InventarioKiosco.query.filter_by(kiosco_id=id_kiosco).all()
        for item in inventarios:
            item.cantidad = 50

        # Regla de Negocio: Si la bóveda de dinero sigue llena, mantenemos esa alerta.
        # Si el dinero está bien, regresamos el nodo a Operativo.
        if kiosco.efectivo_acumulado >= 3000:
            kiosco.estado = 'Saturado (Efectivo)'
        else:
            kiosco.estado = 'Operativo'

        db.session.commit()
        
        return jsonify({"estado": "Éxito", "mensaje": f"Ruta logística completada: Stock al 100% en {kiosco.ubicacion}."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"estado": "Error", "mensaje": str(e)})
# ==========================================
# ARRANQUE DEL SERVIDOR
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)