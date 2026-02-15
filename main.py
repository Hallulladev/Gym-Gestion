import sys
from PyQt6.QtWidgets import QApplication
from Loggin import LoginWindow
from proyecto import GymWindow, inicialize_database


def main() -> None:
    # Inicializar la base de datos antes de todo
    inicialize_database()

    app = QApplication(sys.argv)

    # Mostrar ventana de login (QDialog)
    login = LoginWindow()

    # exec() devuelve QDialog.DialogCode.Accepted (1) si se aceptó
    if login.exec():
        # Login exitoso: abrir la ventana principal
        window = GymWindow()
        window.show()
        sys.exit(app.exec())
    else:
        # Login cancelado o fallido
        sys.exit(0)


if __name__ == "__main__":
    main()