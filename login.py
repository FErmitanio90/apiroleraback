from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from datetime import timedelta
import sqlite3
from SRC.connect_sqlite import get_db_connection, close_db_connection  # ✅ import correcto

# 🧩 Blueprint
login_bp = Blueprint("login_bp", __name__)

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

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Base de datos no disponible"}), 503

    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT iduser, username, nombre, apellido, password FROM users WHERE username = ?",
            (username,)
        )
        row = cursor.fetchone()

        if not row:
            return jsonify({"error": "Usuario no encontrado"}), 404

        user = {
            "iduser": row[0],
            "username": row[1],
            "nombre": row[2],
            "apellido": row[3],
            "password": row[4]
        }

        if user["password"] != password:
            return jsonify({"error": "Contraseña incorrecta"}), 401

        claims = {
            "username": user["username"],
            "nombre": user["nombre"],
            "apellido": user["apellido"]
        }

        access_token = create_access_token(
            identity=str(user["iduser"]),
            additional_claims=claims,
            expires_delta=timedelta(hours=1)
        )

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

    except sqlite3.Error as db_err:
        print(f"❌ Error de SQLite: {db_err}")
        return jsonify({"error": "Error de base de datos", "detalle": str(db_err)}), 500

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return jsonify({"error": "Error interno del servidor", "detalle": str(e)}), 500

    finally:
        close_db_connection(conn)


