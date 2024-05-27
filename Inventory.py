import sys
import sqlite3
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QDialog,
    QFormLayout,
    QDialogButtonBox,
    QGridLayout,
    QSpacerItem,
    QSizePolicy,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt, QRegExp, QAbstractTableModel, QModelIndex, QVariant
from PyQt5.QtGui import QFont, QIcon, QColor, QRegExpValidator, QValidator

DATABASE_PATH = "store.db"

class InventoryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clothing Store Inventory Management")
        self.setWindowIcon(QIcon("store.png"))  # Replace "store.png" with your icon file
        self._create_database()
        self._init_ui()

    def _create_database(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL
            )
        """)
        conn.commit()
        conn.close()

    def _init_ui(self):
        # Fonts
        font_title = QFont("Arial", 24, QFont.Bold)
        font_label = QFont("Arial", 14)
        font_table = QFont("Arial", 12)

        # Title
        title_label = QLabel("Clothing Store Inventory", self)
        title_label.setFont(font_title)
        title_label.setAlignment(Qt.AlignCenter)

        # Input Fields
        self.name_entry = QLineEdit(self)
        self.name_entry.setPlaceholderText("Item Name")
        self.price_entry = QLineEdit(self)
        self.price_entry.setPlaceholderText("Item Price")
        self.price_entry.setValidator(QRegExpValidator(QRegExp("[0-9]*\.?[0-9]*")))
        self.quantity_entry = QLineEdit(self)
        self.quantity_entry.setPlaceholderText("Item Quantity")
        self.quantity_entry.setValidator(QRegExpValidator(QRegExp("[0-9]*")))

        # Buttons
        add_button = QPushButton("Add Item", self)
        add_button.clicked.connect(self._add_item)
        delete_button = QPushButton("Delete Item", self)
        delete_button.clicked.connect(self._delete_item)
        edit_button = QPushButton("Edit Item", self)
        edit_button.clicked.connect(self._edit_item)
        add_many_button = QPushButton("Add Multiple Items", self)
        add_many_button.clicked.connect(self._open_add_many_dialog)
        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self._search_items)
        self.search_entry = QLineEdit(self)
        self.search_entry.setPlaceholderText("Search by Name or ID")

        # Table
        self.item_table = QTableWidget(self)
        self.item_table.setColumnCount(4)
        self.item_table.setHorizontalHeaderLabels(
            ["ID", "Name", "Price", "Quantity"]
        )
        self.item_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.item_table.setFont(font_table)
        self.item_table.setAlternatingRowColors(True)  # Alternate row colors
        self.item_table.setSelectionBehavior(QAbstractItemView.SelectRows)  # Select whole rows
        self.item_table.cellChanged.connect(self._update_item)

        # Layouts
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.name_entry)
        input_layout.addWidget(self.price_entry)
        input_layout.addWidget(self.quantity_entry)

        button_layout = QHBoxLayout()
        button_layout.addWidget(add_button)
        button_layout.addWidget(delete_button)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(add_many_button)
        button_layout.addWidget(self.search_entry)
        button_layout.addWidget(search_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addSpacing(10)
        main_layout.addLayout(input_layout)
        main_layout.addSpacing(10)
        main_layout.addLayout(button_layout)
        main_layout.addSpacing(10)
        main_layout.addWidget(self.item_table)
        self.setLayout(main_layout)

        # Style the table
        self.item_table.setStyleSheet("""
            QTableWidget {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
            }
            QHeaderView::section {
                background-color: #eee;
                border: 1px solid #ccc;
                padding: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #ddd;
            }
        """)

        self._load_items()

    def _load_items(self):
        self.item_table.setRowCount(0)
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items ORDER BY id")
        items = cursor.fetchall()
        conn.close()

        if items:
            for row_number, item in enumerate(items):
                self.item_table.insertRow(row_number)
                for column_number, data in enumerate(item):
                    self.item_table.setItem(
                        row_number, column_number, QTableWidgetItem(str(data))
                    )
        else:
            self.item_table.setRowCount(1)
            self.item_table.setItem(
                0, 0, QTableWidgetItem("No items found. Start adding items!")
            )
            self.item_table.item(0, 0).setTextAlignment(Qt.AlignCenter)

    def _add_item(self):
        name = self.name_entry.text()
        price = self.price_entry.text()
        quantity = self.quantity_entry.text()

        if not all([name, price, quantity]):
            QMessageBox.warning(self, "Error", "Please fill all fields.")
            return

        try:
            price = float(price)
            if price <= 0:
                raise ValueError
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(
                self, "Error", "Invalid price or quantity format. Must be positive."
            )
            return

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO items (name, price, quantity) VALUES (?, ?, ?)",
                (name, price, quantity),
            )
            conn.commit()
            self._clear_input_fields()
            self._load_items()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "An item with that name already exists.")
        conn.close()

    def _delete_item(self):
        selected_row = self.item_table.currentRow()
        if selected_row >= 0:
            item_id = self.item_table.item(selected_row, 0).text()
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
            conn.commit()
            conn.close()
            self.item_table.removeRow(selected_row)
            self._renumber_ids()
        else:
            QMessageBox.warning(self, "Error", "Please select an item to delete.")

    def _edit_item(self):
        selected_row = self.item_table.currentRow()
        if selected_row >= 0:
            item_id = self.item_table.item(selected_row, 0).text()
            name = self.item_table.item(selected_row, 1).text()
            price = self.item_table.item(selected_row, 2).text()
            quantity = self.item_table.item(selected_row, 3).text()

            dialog = EditItemDialog(self, item_id, name, price, quantity)
            if dialog.exec_() == QDialog.Accepted:
                self._load_items()
        else:
            QMessageBox.warning(self, "Error", "Please select an item to edit.")

    def _search_items(self):
        search_term = self.search_entry.text()
        if not search_term:
            self._load_items()
            return

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM items WHERE name LIKE ? OR id = ?",
            (f"%{search_term}%", search_term),
        )
        items = cursor.fetchall()
        conn.close()

        self.item_table.setRowCount(0)
        for row_number, item in enumerate(items):
            self.item_table.insertRow(row_number)
            for column_number, data in enumerate(item):
                self.item_table.setItem(
                    row_number, column_number, QTableWidgetItem(str(data))
                )

    def _clear_input_fields(self):
        self.name_entry.clear()
        self.price_entry.clear()
        self.quantity_entry.clear()

    def _open_add_many_dialog(self):
        dialog = AddManyItemsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self._load_items()

    def _update_item(self, row, column):
        if column == 0:  # Don't allow ID to be edited
            return

        item_id = self.item_table.item(row, 0).text()
        new_value = self.item_table.item(row, column).text()

        try:
            if column == 2:  # Price
                new_value = float(new_value)
            elif column == 3:  # Quantity
                new_value = int(new_value)
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid data format.")
            return

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        if column == 1:  # Name
            try:
                cursor.execute(
                    "UPDATE items SET name = ? WHERE id = ?", (new_value, item_id)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                QMessageBox.warning(
                    self, "Error", "An item with that name already exists."
                )
                conn.rollback()
                self._load_items()  # Reload to revert changes
        elif column == 2:  # Price
            cursor.execute(
                "UPDATE items SET price = ? WHERE id = ?", (new_value, item_id)
            )
            conn.commit()
        elif column == 3:  # Quantity
            cursor.execute(
                "UPDATE items SET quantity = ? WHERE id = ?", (new_value, item_id)
            )
            conn.commit()

        conn.close()

    def _renumber_ids(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM items ORDER BY id")
        ids = cursor.fetchall()

        if ids:
            for i, (id,) in enumerate(ids):
                if i + 1 != id:
                    cursor.execute("UPDATE items SET id = ? WHERE id = ?", (i + 1, id))
            conn.commit()
            self._load_items()
            self._reset_autoincrement()

        conn.close()

    def _reset_autoincrement(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) FROM items")
        max_id = cursor.fetchone()[0]
        if max_id is not None:
            cursor.execute("UPDATE sqlite_sequence SET seq = ?", (max_id,))
        conn.commit()
        conn.close()

class AddManyItemsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Multiple Items")
        self.setWindowIcon(QIcon("store.png"))

        self.layout = QVBoxLayout()
        self.grid_layout = QGridLayout()
        self.grid_layout.setColumnStretch(1, 1)  # Stretch column for Name
        self.grid_layout.setColumnStretch(3, 1)  # Stretch column for Price
        self.grid_layout.setColumnStretch(5, 1)  # Stretch column for Quantity

        # Add initial row
        self._add_item_row()

        # Buttons
        add_row_button = QPushButton("Add Row")
        add_row_button.clicked.connect(self._add_item_row)
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_items)
        button_box.rejected.connect(self.reject)

        # Layout
        self.layout.addWidget(QLabel("Add Multiple Items:"))  # Title
        self.layout.addLayout(self.grid_layout)
        self.layout.addWidget(add_row_button)
        self.layout.addWidget(button_box)

        self.setLayout(self.layout)

    def _add_item_row(self):
        row_count = self.grid_layout.rowCount()
        name_entry = QLineEdit()
        price_entry = QLineEdit()
        price_entry.setValidator(QRegExpValidator(QRegExp("[0-9]*\.?[0-9]*")))
        quantity_entry = QLineEdit()
        quantity_entry.setValidator(QRegExpValidator(QRegExp("[0-9]*")))

        self.grid_layout.addWidget(QLabel("Name:"), row_count, 0)
        self.grid_layout.addWidget(name_entry, row_count, 1)
        self.grid_layout.addWidget(QLabel("Price:"), row_count, 2)
        self.grid_layout.addWidget(price_entry, row_count, 3)
        self.grid_layout.addWidget(QLabel("Quantity:"), row_count, 4)
        self.grid_layout.addWidget(quantity_entry, row_count, 5)

    def _save_items(self):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        existing_names = set()

        for row in range(self.grid_layout.rowCount()):
            name_entry = self.grid_layout.itemAtPosition(row, 1).widget()
            price_entry = self.grid_layout.itemAtPosition(row, 3).widget()
            quantity_entry = self.grid_layout.itemAtPosition(row, 5).widget()

            name = name_entry.text()
            price = price_entry.text()
            quantity = quantity_entry.text()

            if all([name, price, quantity]):
                try:
                    price = float(price)
                    if price <= 0:
                        raise ValueError
                    quantity = int(quantity)
                    if quantity <= 0:
                        raise ValueError
                    if name in existing_names:
                        QMessageBox.warning(
                            self,
                            "Error",
                            f"An item with the name '{name}' already exists in the database. Skipping row {row + 1}.",
                        )
                        continue  # Skip this row if name already exists
                    else:
                        existing_names.add(name)
                        cursor.execute(
                            "INSERT INTO items (name, price, quantity) VALUES (?, ?, ?)",
                            (name, price, quantity),
                        )
                except ValueError:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"Invalid data for row {row + 1}. Skipping.",
                    )
                    conn.rollback()
                    return
                except sqlite3.IntegrityError:
                    QMessageBox.warning(
                        self,
                        "Error",
                        f"An item with the name '{name}' already exists in the database. Skipping row {row + 1}.",
                    )
                    conn.rollback()
                    return
            else:
                QMessageBox.warning(
                    self, "Error", f"Incomplete data for row {row + 1}. Skipping."
                )
                conn.rollback()
                return

        conn.commit()
        conn.close()
        self.accept()

class EditItemDialog(QDialog):
    def __init__(self, parent=None, item_id=None, name=None, price=None, quantity=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Item")
        self.setWindowIcon(QIcon("store.png"))

        self.item_id = item_id
        self.layout = QFormLayout()

        self.name_entry = QLineEdit(name)
        self.price_entry = QLineEdit(price)
        self.price_entry.setValidator(QRegExpValidator(QRegExp("[0-9]*\.?[0-9]*")))
        self.quantity_entry = QLineEdit(quantity)
        self.quantity_entry.setValidator(QRegExpValidator(QRegExp("[0-9]*")))

        self.layout.addRow("Name:", self.name_entry)
        self.layout.addRow("Price:", self.price_entry)
        self.layout.addRow("Quantity:", self.quantity_entry)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._save_changes)
        button_box.rejected.connect(self.reject)

        self.layout.addWidget(button_box)
        self.setLayout(self.layout)

    def _save_changes(self):
        name = self.name_entry.text()
        price = self.price_entry.text()
        quantity = self.quantity_entry.text()

        if not all([name, price, quantity]):
            QMessageBox.warning(self, "Error", "Please fill all fields.")
            return

        try:
            price = float(price)
            if price <= 0:
                raise ValueError
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid price or quantity format. Must be positive.")
            return

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE items SET name = ?, price = ?, quantity = ? WHERE id = ?",
                (name, price, quantity, self.item_id),
            )
            conn.commit()
            self.accept()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "An item with that name already exists.")
            conn.rollback()
        conn.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InventoryApp()
    window.show()
    sys.exit(app.exec_())