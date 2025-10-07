import sqlite3

try:
    # Conexión (se creará la base si no existe)
    miConexion = sqlite3.connect("Database/baseApiRolMaster.db")
    cursor = miConexion.cursor()

    # Activar claves foráneas (por defecto están desactivadas en SQLite)
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Crear tabla users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        iduser INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre VARCHAR(50) NOT NULL,
        apellido VARCHAR(50) NOT NULL,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(50) NOT NULL
    );
    """)

    # Crear tabla dashboard
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

    # Guardar los cambios
    miConexion.commit()
    print("Base de datos y tablas creadas correctamente ✅")

except Exception as e:
    print(f"Error al crear la base de datos: {e}")

finally:
    # Cerrar la conexión
    if miConexion:
        miConexion.close()
