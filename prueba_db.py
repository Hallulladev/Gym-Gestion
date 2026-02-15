"""
Utilidad para verificar el estado de la base de datos del gimnasio.
Muestra información sobre la tabla de socios y los registros almacenados.
"""

import sqlite3
import os

DB_FILE = "gym_members.db"


def check_database() -> None:
    """Verifica y muestra información de la base de datos del gimnasio."""

    # Verificar si el archivo existe
    if not os.path.exists(DB_FILE):
        print(f"[!] El archivo '{DB_FILE}' no existe.")
        return

    print(f"[+] Archivo encontrado: {DB_FILE}")
    print(f"    Tamaño: {os.path.getsize(DB_FILE):,} bytes\n")

    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Verificar si existe la tabla members
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='members';"
        )
        if cursor.fetchone() is None:
            print("[!] La tabla 'members' NO existe en la base de datos.")
            return

        print("[+] La tabla 'members' existe.\n")

        # Contar registros
        cursor.execute("SELECT COUNT(*) FROM members")
        count = cursor.fetchone()[0]
        print(f"[+] Total de socios registrados: {count}\n")

        if count == 0:
            print("    (No hay socios para mostrar)")
            return

        # Mostrar los socios
        cursor.execute("SELECT id, name, age, membership, price FROM members")
        rows = cursor.fetchall()

        print("-" * 70)
        print(f"{'ID':<5} {'Nombre':<25} {'Edad':<6} {'Membresía':<12} {'Precio':>10}")
        print("-" * 70)
        for row in rows:
            member_id, name, age, membership, price = row
            print(f"{member_id:<5} {name:<25} {age:<6} {membership:<12} ${price:>9,.2f}")
        print("-" * 70)

    except sqlite3.Error as e:
        print(f"[ERROR] Fallo en la base de datos: {e}")
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    check_database()
