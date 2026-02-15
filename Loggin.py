from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
import sqlite3

class LoginWindow(QDialog):
    """Ventana de login conectada a SQLite para el sistema de gimnasio."""

    def __init__(self) -> None:
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle("Acceso al Sistema - Gym")
        self.setFixedSize(320, 220) # Aumentamos un poco el alto para el nuevo botón

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Bienvenido")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")

        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuario")

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Contraseña")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)

        # Botón de Entrar
        self.login_button = QPushButton("Entrar")
        self.login_button.clicked.connect(self.check_credentials)

        # Botón de Registrarse (AQUÍ ESTÁ EL ARREGLO)
        self.register_button = QPushButton("Crear Cuenta")
        self.register_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.register_button.clicked.connect(self.register_user)

        layout.addWidget(title)
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(self.login_button)
        layout.addWidget(self.register_button) # IMPORTANTE: Agregarlo al layout

        self.setLayout(layout)

    def check_credentials(self) -> None:
        """Valida las credenciales consultando la base de datos."""
        user = self.user_input.text().strip()
        password = self.pass_input.text()

        try:
            conn = sqlite3.connect("gym_members.db")
            cursor = conn.cursor()
            # Buscamos al usuario en la tabla users
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (user, password))
            result = cursor.fetchone()
            conn.close()

            if result:
                self.accept() # Éxito
            else:
                QMessageBox.warning(self, "Error", "Usuario o clave incorrectos")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error de BD", f"No se pudo conectar: {e}")

    def register_user(self) -> None:
        """Registra un nuevo usuario en la base de datos."""
        user = self.user_input.text().strip()
        password = self.pass_input.text()

        if not user or not password:
            QMessageBox.warning(self, "Campos Vacíos", "Por favor llena ambos campos")
            return

        try:
            conn = sqlite3.connect("gym_members.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, password))
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Éxito", f"Usuario '{user}' creado. ¡Ya puedes entrar!")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Ese nombre de usuario ya existe")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error de BD", f"Error al registrar: {e}")