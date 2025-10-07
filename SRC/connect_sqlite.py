# src/connect_sqlite.py
import sqlite3
import os

# 📂 Ruta absoluta para evitar errores en Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "Database", "baseApiRolMaster.db")

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        print(f"✅ Conectado a SQLite en {DB_PATH}")
        return conn
    except sqlite3.Error as e:
        print(f"❌ Error al conectar SQLite: {e}")
        return None

def close_db_connection(conn):
    if conn:
        conn.close()

# 🧱 Crear tablas si no existen
def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA foreign_keys = ON;")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            iduser INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre VARCHAR(50) NOT NULL,
            apellido VARCHAR(50) NOT NULL,
            username VARCHAR(50) NOT NULL UNIQUE,
            password VARCHAR(50) NOT NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dashboard (
            idsesion INTEGER PRIMARY KEY AUTOINCREMENT,
            iduser INTEGER NOT NULL,
            cronica VARCHAR(50) NOT NULL,
            numero_de_sesion INTEGER NOT NULL,
            fecha DATETIME NOT NULL,
            resumen TEXT,
            FOREIGN KEY (iduser) REFERENCES users(iduser) ON DELETE CASCADE
        );
        """)

        conn.commit()
        print("✅ Base de datos y tablas listas")

    except Exception as e:
        print(f"❌ Error al inicializar DB: {e}")
    finally:
        close_db_connection(conn)

# Ejecutar creación al importar
init_db()

