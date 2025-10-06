from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import mysql.connector

# Importar Blueprints
from login import login_bp
from dashboard import sesion 
from users import usuario 

app = Flask(__name__)
CORS(app, 
     resources={r"/*": {"origins": "http://localhost:5000"}}, # Cambia 5000 si es diferente
     allow_headers=["Authorization", "Content-Type"],
     supports_credentials=True)


# Configuración JWT centralizada
app.config["JWT_SECRET_KEY"] = "clave-super-secreta-de-master-rol"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600  # 1 hora
app.config["JWT_TOKEN_LOCATION"] = ["headers"] 

jwt = JWTManager(app)

# Configuración DB
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1',
    'database': 'AppMasterRol',
    'port': 3306
}

def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"❌ Error al conectar a MySQL: {err}")
        return None

def close_db_connection(conn):
    if conn and conn.is_connected():
        conn.close()

#  Registro de blueprints
app.register_blueprint(login_bp, url_prefix="/")  # Rutas de login

# Datos simulados (pueden ser reemplazados por DB)
usuarios = [usuario]
dashboards = [sesion]

#  Rutas protegidas con JWT
@app.route("/perfil", methods=["GET"])
@jwt_required()
def perfil():
    """Ruta protegida: Devuelve el perfil del usuario autenticado."""
    iduser = get_jwt_identity()
    return jsonify({
        "msg": "Accediste al perfil",
        "iduser": iduser
    }), 200

# CRUD de Usuarios
@app.route("/users", methods=["GET"])
@jwt_required()
def get_users():
    """Listar usuarios (requiere token)."""
    return jsonify(usuarios), 200

@app.route("/users", methods=["POST"])
def create_user():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Servicio de base de datos no disponible"}), 503

    cursor = conn.cursor(dictionary=True)
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Petición inválida. Se requiere JSON."}), 400

        required_fields = ['nombre', 'apellido', 'username', 'password']
        for field in required_fields:
            if field not in data or not data[field].strip():
                return jsonify({"error": f"Falta el campo requerido: {field}"}), 400

        sql = """INSERT INTO users (nombre, apellido, username, password)
                 VALUES (%s, %s, %s, %s)"""
        values = (data['nombre'], data['apellido'], data['username'], data['password'])
        cursor.execute(sql, values)
        conn.commit()

        user_id = cursor.lastrowid
        return jsonify({
            "mensaje": "Usuario creado exitosamente",
            "usuario": {
                "iduser": user_id,
                "nombre": data['nombre'],
                "username": data['username']
            }
        }), 201

    except mysql.connector.Error as db_err:
        print(f"❌ Error MySQL: {db_err}")
        return jsonify({"error": "Error en la base de datos", "detalle": str(db_err)}), 500

    finally:
        cursor.close()
        close_db_connection(conn)

# 📊 CRUD de Dashboard

@app.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    # 1. Obtener el ID del usuario para filtrar
    iduser = get_jwt_identity()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"msg": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor(dictionary=True)

        # SQL: Usamos la tabla 'dashboard', 'idsesion' (PK) y filtramos por 'iduser'
        sql = """
        SELECT idsesion, cronica, numero_de_sesion, fecha, resumen 
        FROM dashboard 
        WHERE iduser = %s 
        ORDER BY fecha DESC
        """
        
        # Ejecutar la consulta filtrando por el iduser
        cursor.execute(sql, (iduser,)) 
        sesiones = cursor.fetchall()
        
        return jsonify(sesiones), 200

    except mysql.connector.Error as err:
        print(f"❌ Error MySQL al seleccionar: {err}")
        return jsonify({"msg": f"Error de base de datos: {err.msg}"}), 500
    except Exception as e:
        print(f"❌ Error al procesar GET: {e}")
        return jsonify({"msg": "Error interno del servidor"}), 500
    finally:
        close_db_connection(conn)

@app.route("/dashboard", methods=["POST"])
@jwt_required()
def handle_dashboard_post():
    # 1. Obtener el ID del usuario del token JWT
    iduser = get_jwt_identity() 
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"msg": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()
        accion = request.form.get('accion') 
        
        if accion == 'eliminar':
            id_sesion_a_eliminar = request.form.get('id')
            
            if not id_sesion_a_eliminar:
                # Si el ID no se encuentra en el formulario, es un error del frontend.
                print("❌ Advertencia: ID de sesión no proporcionado en el formulario de eliminación.")
                # Si estás usando Flask y no una API pura, usa flash y redirect
                # flash('Error: El ID de la sesión a eliminar no fue proporcionado.', 'danger')
                return jsonify({"msg": "Error: ID de sesión no proporcionado"}), 400 

            # SQL: ELIMINACIÓN
            sql_delete = """
            DELETE FROM dashboard 
            WHERE idsesion = %s AND iduser = %s
            """
            cursor.execute(sql_delete, (id_sesion_a_eliminar, iduser))
            conn.commit()
            
            # Verificamos si se eliminó alguna fila
            if cursor.rowcount == 0:
                print(f"❌ Fallo al eliminar: Sesión con ID {id_sesion_a_eliminar} no encontrada o no pertenece al usuario {iduser}.")

                return jsonify({"msg": "Sesión no encontrada o no autorizada"}), 404 
            
            print(f"✅ Sesión {id_sesion_a_eliminar} eliminada exitosamente por usuario {iduser}")
            return jsonify({"msg": "Sesión eliminada exitosamente"}), 200

        # LÓGICA DE CREACIÓN (Maneja la solicitud JSON original)
        
        # Si no es la acción 'eliminar', asumimos que es una solicitud de creación JSON.
        if not request.is_json:
            return jsonify({"msg": "Solicitud POST inválida. Esperado JSON o acción 'eliminar'."}), 400

        data = request.json
        
        # SQL: Usamos la tabla 'dashboard' e incluimos 'iduser'
        sql_insert = """
        INSERT INTO dashboard (iduser, cronica, numero_de_sesion, fecha, resumen)
        VALUES (%s, %s, %s, %s, %s)
        """
        val = (
            iduser, 
            data.get('cronica'),
            int(data.get('numero_de_sesion')),
            data.get('fecha'),
            data.get('resumen')
        )

        cursor.execute(sql_insert, val)
        conn.commit() 
        print(f"🎉 COMMIT EXITOSO en tabla 'dashboard' para iduser: {iduser}")
        
        return jsonify({"msg": "Sesión creada exitosamente"}), 201

    except mysql.connector.Error as err:
        print(f"❌ ERROR CRÍTICO MySQL: {err}")
        return jsonify({"msg": f"Error de base de datos: {err.msg}"}), 500
    except Exception as e:
        print(f"❌ ERROR Python General: {e}")
        return jsonify({"msg": "Error interno del servidor"}), 500
    finally:
        close_db_connection(conn)

@app.route("/dashboard/<int:idsesion>", methods=["DELETE"])
@jwt_required()
def delete_dashboard_session(idsesion):
    # 1. Obtener el ID del usuario del token JWT para la seguridad
    iduser = get_jwt_identity()
    
    conn = get_db_connection()
    if not conn:
        return jsonify({"msg": "Error de conexión a la base de datos"}), 500

    try:
        cursor = conn.cursor()
        sql_delete = """
        DELETE FROM dashboard 
        WHERE idsesion = %s AND iduser = %s
        """
        
        # Ejecutamos la consulta con los parámetros (idsesion es el entero capturado de la URL)
        cursor.execute(sql_delete, (idsesion, iduser))
        conn.commit()
        
        # 2. Verificamos si se eliminó alguna fila
        if cursor.rowcount == 0:
            print(f"❌ Fallo al eliminar: Sesión {idsesion} no encontrada o no pertenece al usuario {iduser}.")
            return jsonify({"msg": "Sesión no encontrada o no autorizada"}), 404 
        
        print(f"✅ Sesión {idsesion} eliminada exitosamente por usuario {iduser}")
        return jsonify({"msg": "Sesión eliminada exitosamente"}), 200

    except mysql.connector.Error as err:
        print(f"❌ ERROR CRÍTICO MySQL al eliminar: {err}")
        return jsonify({"msg": f"Error de base de datos: {err.msg}"}), 500
    except Exception as e:
        print(f"❌ ERROR Python General: {e}")
        return jsonify({"msg": "Error interno del servidor"}), 500
    finally:
        close_db_connection(conn)

# RUTA: PUT /dashboard/<int:idsesion> (Actualizar sesión - API JSON)
@app.route('/dashboard', methods=['PUT'])
def editar_sesion():
    data = request.get_json()
    print("[DEBUG BACK] PUT recibido:", data)

    id_sesion = data.get("idsesion")
    if not id_sesion:
        return jsonify({"error": "Falta ID"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE dashboard
            SET cronica=%s, numero_de_sesion=%s, fecha=%s, resumen=%s
            WHERE idsesion=%s
        """, (data.get("cronica"), data.get("numero_de_sesion"), data.get("fecha"), data.get("resumen"), id_sesion))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({"error": "Sesión no encontrada"}), 404

        return jsonify({"success": True}), 200
    finally:
        cursor.close()
        conn.close()

# Inicio del servidor
if __name__ == "__main__":
    app.run(debug=True, port=5001)
