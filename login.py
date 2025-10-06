from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta
import mysql.connector

# 🧩 Blueprint
login_bp = Blueprint("login_bp", __name__)

# 📡 Configuración DB
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root1',
    'database': 'AppMasterRol',
    'port': 3306
}

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# -----------------------------------------
# 🔐 Ruta de Login
# -----------------------------------------
@login_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Se requiere un cuerpo JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan datos: username y password"}), 400

    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # ⚠️ Comparación simple (en producción usar hash seguro)
        if user["password"] != password:
            return jsonify({"error": "Contraseña incorrecta"}), 401

        # 🧾 Claims opcionales (datos extra dentro del token)
        claims = {
            "username": user["username"],
            "nombre": user["nombre"],
            "apellido": user["apellido"]
        }

        # 🪙 Generar token con ID como string (requerido por JWT)
        access_token = create_access_token(
            identity=str(user["iduser"]),      # ✅ identity debe ser string
            additional_claims=claims,          # ℹ️ datos extra accesibles con get_jwt()
            expires_delta=timedelta(hours=1)   # ⏱️ expira en 1 hora
        )

        # 🧾 Devolver token + info usuario
        return jsonify({
            "success": True,
            "msg": "Login exitoso",
            "access_token": access_token,
            "usuario": {
                "iduser": user["iduser"],
                "username": user["username"],
                "nombre": user["nombre"],
                "apellido": user["apellido"]
            }
        }), 200

    except mysql.connector.Error as db_err:
        print(f"❌ Error de MySQL: {db_err}")
        return jsonify({"error": "Error de base de datos", "detalle": str(db_err)}), 500

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

    finally:
        if conn:
            conn.close()
