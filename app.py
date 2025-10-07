from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
import sqlite3

# ✅ Importar conexión centralizada
from SRC.connect_sqlite import get_db_connection, close_db_connection

# Importar Blueprints
from login import login_bp
from dashboard import sesion
from users import usuario

# Crear app Flask
app = Flask(__name__)
CORS(app,
     resources={r"/*": {"origins": "http://localhost:5000"}},
     allow_headers=["Authorization", "Content-Type"],
     supports_credentials=True
)

# Configuración JWT
app.config["JWT_SECRET_KEY"] = "clave-super-secreta-de-master-rol"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 3600
app.config["JWT_TOKEN_LOCATION"] = ["headers"]
jwt = JWTManager(app)

# 🔗 Registrar blueprints
app.register_blueprint(login_bp, url_prefix="/")

# Datos simulados (si los usas)
usuarios = [usuario]
dashboards = [sesion]

# 🧱 Rutas
@app.route("/perfil", methods=["GET"])
@jwt_required()
def perfil():
    iduser = get_jwt_identity()
    return jsonify({
        "msg": "Accediste al perfil",
        "iduser": iduser
    }), 200

@app.route("/users", methods=["POST"])
def create_user():
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Base de datos no disponible"}), 503
    cursor = conn.cursor()
    try:
        data = request.get_json()
        required_fields = ['nombre', 'apellido', 'username', 'password']
        for f in required_fields:
            if f not in data:
                return jsonify({"error": f"Falta campo {f}"}), 400
        cursor.execute("""
            INSERT INTO users (nombre, apellido, username, password)
            VALUES (?, ?, ?, ?)
        """, (data['nombre'], data['apellido'], data['username'], data['password']))
        conn.commit()
        return jsonify({"msg": "Usuario creado exitosamente"}), 201
    except sqlite3.Error as e:
        return jsonify({"error": f"SQLite: {e}"}), 500
    finally:
        close_db_connection(conn)

@app.route("/dashboard", methods=["GET"])
@jwt_required()
def get_dashboard():
    iduser = get_jwt_identity()
    conn = get_db_connection()
    if not conn:
        return jsonify({"msg": "Error DB"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT idsesion, cronica, numero_de_sesion, fecha, resumen
            FROM dashboard WHERE iduser = ? ORDER BY fecha DESC
        """, (iduser,))
        sesiones = [dict(row) for row in cursor.fetchall()]
        return jsonify(sesiones), 200
    finally:
        close_db_connection(conn)

@app.route("/dashboard", methods=["POST"])
@jwt_required()
def create_dashboard():
    iduser = get_jwt_identity()
    conn = get_db_connection()
    if not conn:
        return jsonify({"msg": "Error DB"}), 500
    try:
        data = request.get_json()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dashboard (iduser, cronica, numero_de_sesion, fecha, resumen)
            VALUES (?, ?, ?, ?, ?)
        """, (iduser, data.get('cronica'), data.get('numero_de_sesion'), data.get('fecha'), data.get('resumen')))
        conn.commit()
        return jsonify({"msg": "Sesión creada"}), 201
    finally:
        close_db_connection(conn)

@app.route("/dashboard/<int:idsesion>", methods=["PUT"])
@jwt_required()
def update_dashboard(idsesion):
    iduser = get_jwt_identity()
    conn = get_db_connection()
    if not conn:
        return jsonify({"msg": "Error DB"}), 500
        
    try:
        data = request.get_json()
        
        # 1. Validar que se hayan enviado datos
        if not data:
            return jsonify({"msg": "No se enviaron datos para actualizar."}), 400

        cursor = conn.cursor()
        
        # 2. Construir la consulta SQL dinámicamente
        # Esto permite actualizar solo los campos que el usuario envió
        updates = []
        params = []
        
        # Lista de campos permitidos para actualizar
        allowed_fields = ['cronica', 'numero_de_sesion', 'fecha', 'resumen']
        
        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = ?")
                params.append(data[field])

        if not updates:
            return jsonify({"msg": "No hay campos válidos para actualizar."}), 400

        # Parámetros finales para la cláusula WHERE: el ID de la sesión y el ID del usuario
        params.extend([idsesion, iduser])
        
        update_query = f"""
            UPDATE dashboard SET {', '.join(updates)}
            WHERE idsesion = ? AND iduser = ?
        """
        
        cursor.execute(update_query, tuple(params))
        
        # 3. Verificar si se actualizó alguna fila
        if cursor.rowcount == 0:
             # Retorna 404 si la sesión no existe o si no pertenece al usuario autenticado
             return jsonify({"msg": "Sesión no encontrada o no tienes permiso para editarla."}), 404
             
        conn.commit()
        return jsonify({"msg": "Sesión actualizada exitosamente."}), 200
    
    except Exception as e:
        print(f"Error al actualizar sesión: {e}")
        conn.rollback()
        return jsonify({"msg": "Error interno del servidor", "error": str(e)}), 500
        
    finally:
        close_db_connection(conn)

if __name__ == "__main__":
    app.run(debug=True, port=5000)