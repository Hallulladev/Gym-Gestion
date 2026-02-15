import sys
from typing import Any, Dict, List, Optional
import sqlite3


def inicialize_database() -> None:
	"""Crea la base de datos y las tablas de socios y usuarios si no existen."""
	conn = sqlite3.connect("gym_members.db")
	cursor = conn.cursor()

	# Tabla de socios
	cursor.execute(
		"""
		CREATE TABLE IF NOT EXISTS members (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			age INTEGER NOT NULL,
			membership TEXT NOT NULL,
			price REAL NOT NULL
		)
		"""
	)

	# Tabla de usuarios para login
	cursor.execute(
		"""
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT NOT NULL UNIQUE,
			password TEXT NOT NULL
		)
		"""
	)

	# Insertar usuario admin por defecto si no existe
	cursor.execute(
		"SELECT id FROM users WHERE username = ?", ("admin",)
	)
	if cursor.fetchone() is None:
		cursor.execute(
			"INSERT INTO users (username, password) VALUES (?, ?)",
			("admin", "1234"),
		)

	conn.commit()
	conn.close()


from PyQt6.QtWidgets import (
	QApplication,
	QMainWindow,
	QWidget,
	QVBoxLayout,
	QFormLayout,
	QLineEdit,
	QComboBox,
	QPushButton,
	QTableWidget,
	QTableWidgetItem,
	QMessageBox,
	QHBoxLayout,
	QLabel,
	QGroupBox,
	QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator


class GymWindow(QMainWindow):
	def __init__(self) -> None:
		super().__init__()
		self.setWindowTitle("Gestión de Gimnasio")
		self.setMinimumSize(800, 500)

		self.members: List[Dict[str, Any]] = []
		self.editing_row: Optional[int] = None
		# Precios de los planes de entrenamiento / membresías
		self.membership_prices: Dict[str, float] = {
			"Mensual": 20000.0,
			"Trimestral": 55000.0,
			"Anual": 200000.0,
			"Premium": 300000.0,
		}

		central_widget = QWidget(self)
		self.setCentralWidget(central_widget)

		main_layout = QVBoxLayout()
		main_layout.setContentsMargins(16, 16, 16, 16)
		main_layout.setSpacing(12)
		central_widget.setLayout(main_layout)

		# --- Grupo: Datos del socio ---
		form_group = QGroupBox("Datos del socio")
		form_layout = QFormLayout()
		form_layout.setSpacing(8)
		form_group.setLayout(form_layout)

		self.name_input = QLineEdit()
		self.name_input.setPlaceholderText("Nombre completo del socio")

		self.age_input = QLineEdit()
		self.age_input.setPlaceholderText("Edad")
		self.age_input.setMaxLength(3)
		self.age_input.setValidator(QIntValidator(1, 120, self))

		self.membership_input = QComboBox()
		self.membership_input.addItems([
			"Mensual",
			"Trimestral",
			"Anual",
			"Premium",
		])

		form_layout.addRow("Nombre:", self.name_input)
		form_layout.addRow("Edad:", self.age_input)
		form_layout.addRow("Membresía:", self.membership_input)

		# Label para mostrar el valor del plan seleccionado
		self.price_label = QLabel("")
		self.price_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
		form_layout.addRow("Valor del plan:", self.price_label)

		buttons_layout = QHBoxLayout()
		self.add_button = QPushButton("Agregar socio")
		self.clear_button = QPushButton("Limpiar campos")
		buttons_layout.addStretch(1)
		buttons_layout.addWidget(self.add_button)
		buttons_layout.addWidget(self.clear_button)

		top_layout = QVBoxLayout()
		top_layout.addWidget(form_group)
		top_layout.addLayout(buttons_layout)

		main_layout.addLayout(top_layout)

		self.table = QTableWidget(0, 4)
		self.table.setHorizontalHeaderLabels(["Nombre", "Edad", "Membresía", "Valor a pagar"])
		header = self.table.horizontalHeader()
		header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
		header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
		header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
		header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
		self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
		self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
		self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

		# --- Grupo: Socios registrados ---
		table_group = QGroupBox("Socios registrados")
		table_layout = QVBoxLayout()
		table_layout.setContentsMargins(8, 8, 8, 8)
		table_layout.setSpacing(8)
		table_group.setLayout(table_layout)
		table_layout.addWidget(self.table)

		# Botones para editar/renovar y eliminar socios
		bottom_buttons = QHBoxLayout()
		self.edit_button = QPushButton("Editar / Renovar")
		self.delete_button = QPushButton("Eliminar socio")
		bottom_buttons.addStretch(1)
		bottom_buttons.addWidget(self.edit_button)
		bottom_buttons.addWidget(self.delete_button)
		table_layout.addLayout(bottom_buttons)

		main_layout.addWidget(table_group)

		self.add_button.clicked.connect(self.add_member)
		self.clear_button.clicked.connect(self.clear_fields)
		self.membership_input.currentIndexChanged.connect(self.update_price_label)
		self.edit_button.clicked.connect(self.edit_member)
		self.delete_button.clicked.connect(self.delete_member)

		# Mostrar el precio inicial según la membresía por defecto
		self.update_price_label()
		# Cargar socios previamente guardados en la base de datos
		self.load_members_from_db()

	def add_member(self) -> None:
		name = self.name_input.text().strip()
		age_text = self.age_input.text().strip()
		membership = self.membership_input.currentText()

		if not name:
			self._show_error("El nombre no puede estar vacío.")
			return

		if not age_text.isdigit():
			self._show_error("La edad debe ser un número entero.")
			return

		age = int(age_text)
		if age <= 0 or age > 120:
			self._show_error("La edad debe estar entre 1 y 120 años.")
			return

		price = self.membership_prices.get(membership, 0.0)

		# Si estamos editando un socio existente, actualizamos esa fila y la BD
		if self.editing_row is not None and 0 <= self.editing_row < self.table.rowCount():
			row = self.editing_row
			current_member = self.members[row]
			member_id = current_member.get("id")
			if member_id is not None:
				if not self._update_member_in_db(member_id, name, age, membership, price):
					return
			member = {
				"id": member_id,
				"name": name,
				"age": age,
				"membership": membership,
				"price": price,
			}
			self.members[row] = member
		else:
			# Alta de un nuevo socio (insertar en BD primero)
			member_id = self._insert_member_in_db(name, age, membership, price)
			if member_id == -1:
				return
			member = {
				"id": member_id,
				"name": name,
				"age": age,
				"membership": membership,
				"price": price,
			}
			row = self.table.rowCount()
			self.members.append(member)
			self.table.insertRow(row)

		self.table.setItem(row, 0, QTableWidgetItem(name))
		self.table.setItem(row, 1, QTableWidgetItem(str(age)))
		self.table.setItem(row, 2, QTableWidgetItem(membership))
		self.table.setItem(row, 3, QTableWidgetItem(self._format_price(price)))

		self.editing_row = None
		self.add_button.setText("Agregar socio")
		self.clear_fields()

	def clear_fields(self) -> None:
		self.name_input.clear()
		self.age_input.clear()
		self.membership_input.setCurrentIndex(0)
		self.name_input.setFocus(Qt.FocusReason.OtherFocusReason)
		self.editing_row = None
		self.add_button.setText("Agregar socio")
		self.update_price_label()

	def _show_error(self, message: str) -> None:
		msg = QMessageBox(self)
		msg.setIcon(QMessageBox.Icon.Warning)
		msg.setWindowTitle("Datos inválidos")
		msg.setText(message)
		msg.exec()

	def edit_member(self) -> None:
		row = self.table.currentRow()
		if row < 0 or row >= self.table.rowCount():
			self._show_error("Selecciona un socio de la tabla para editar/renovar.")
			return

		member = self.members[row]
		self.name_input.setText(str(member["name"]))
		self.age_input.setText(str(member["age"]))
		idx = self.membership_input.findText(str(member["membership"]))
		if idx >= 0:
			self.membership_input.setCurrentIndex(idx)

		self.editing_row = row
		self.add_button.setText("Guardar cambios")
		self.name_input.setFocus(Qt.FocusReason.OtherFocusReason)
		self.update_price_label()

	def delete_member(self) -> None:
		row = self.table.currentRow()
		if row < 0 or row >= self.table.rowCount():
			self._show_error("Selecciona un socio de la tabla para eliminar.")
			return

		confirm = QMessageBox.question(
			self,
			"Confirmar eliminación",
			"¿Seguro que deseas eliminar este socio?",
			QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
			QMessageBox.StandardButton.No,
		)

		if confirm == QMessageBox.StandardButton.Yes:
			member = self.members[row]
			member_id = member.get("id")
			if member_id is not None and not self._delete_member_from_db(member_id):
				return
			self.table.removeRow(row)
			if 0 <= row < len(self.members):
				del self.members[row]
			self.editing_row = None
			self.add_button.setText("Agregar socio")
			self.clear_fields()

	def _format_price(self, value: float) -> str:
		"""Devuelve el precio formateado como moneda simple."""
		return f"${value:,.2f}"

	def update_price_label(self) -> None:
		membership = self.membership_input.currentText()
		price = self.membership_prices.get(membership, 0.0)
		self.price_label.setText(self._format_price(price))

	def load_members_from_db(self) -> None:
		"""Carga todos los socios guardados en la base de datos en la tabla."""
		try:
			conn = sqlite3.connect("gym_members.db")
			cursor = conn.cursor()
			cursor.execute("SELECT id, name, age, membership, price FROM members")
			rows = cursor.fetchall()
		finally:
			conn.close()

		self.members.clear()
		self.table.setRowCount(0)
		for member_id, name, age, membership, price in rows:
			member: Dict[str, Any] = {
				"id": member_id,
				"name": name,
				"age": age,
				"membership": membership,
				"price": float(price),
			}
			row = self.table.rowCount()
			self.table.insertRow(row)
			self.members.append(member)
			self.table.setItem(row, 0, QTableWidgetItem(str(name)))
			self.table.setItem(row, 1, QTableWidgetItem(str(age)))
			self.table.setItem(row, 2, QTableWidgetItem(str(membership)))
			self.table.setItem(row, 3, QTableWidgetItem(self._format_price(float(price))))

	def _insert_member_in_db(self, name: str, age: int, membership: str, price: float) -> int:
		"""Inserta un socio en la base de datos y devuelve su id."""
		conn = None
		try:
			conn = sqlite3.connect("gym_members.db")
			cursor = conn.cursor()
			cursor.execute(
				"INSERT INTO members (name, age, membership, price) VALUES (?, ?, ?, ?)",
				(name, age, membership, price),
			)
			conn.commit()
			return int(cursor.lastrowid)
		except sqlite3.Error as e:
			self._show_error(f"Error al guardar en la base de datos: {e}")
			return -1
		finally:
			if conn is not None:
				conn.close()

	def _update_member_in_db(self, member_id: int, name: str, age: int, membership: str, price: float) -> bool:
		"""Actualiza un socio existente en la base de datos."""
		conn = None
		try:
			conn = sqlite3.connect("gym_members.db")
			cursor = conn.cursor()
			cursor.execute(
				"UPDATE members SET name = ?, age = ?, membership = ?, price = ? WHERE id = ?",
				(name, age, membership, price, member_id),
			)
			conn.commit()
			return True
		except sqlite3.Error as e:
			self._show_error(f"Error al actualizar en la base de datos: {e}")
			return False
		finally:
			if conn is not None:
				conn.close()

	def _delete_member_from_db(self, member_id: int) -> bool:
		"""Elimina un socio de la base de datos por id."""
		conn = None
		try:
			conn = sqlite3.connect("gym_members.db")
			cursor = conn.cursor()
			cursor.execute("DELETE FROM members WHERE id = ?", (member_id,))
			conn.commit()
			return True
		except sqlite3.Error as e:
			self._show_error(f"Error al eliminar en la base de datos: {e}")
			return False
		finally:
			if conn is not None:
				conn.close()


def main() -> None:
	inicialize_database()
	app = QApplication(sys.argv)
	window = GymWindow()
	window.show()
	sys.exit(app.exec())


if __name__ == "__main__":
	main()
