import sys
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QScrollArea,
    QComboBox,
    QMessageBox,
    QInputDialog,
    QWidget,
    QVBoxLayout,
    QLabel,
    QTextEdit,
    QDialog,
    QTableWidget,
    QTableWidgetItem,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPainter, QPen, QBrush, QTextDocument, QTextCursor, QTextCharFormat
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
import datetime
import sqlite3

# --- Database Setup ---
DATABASE_PATH = "store.db"

def create_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            quantity INTEGER NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# --- Helper Functions ---

def get_item_by_id(item_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    conn.close()
    return item

def update_item_quantity(item_id, new_quantity):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET quantity = ? WHERE id = ?", (new_quantity, item_id))
    conn.commit()
    conn.close()

# --- Cashier App Functions ---

def load_products():
    products = {}
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM items")
    for row in cursor.fetchall():
        products[row[0]] = {
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'quantity': row[3]
        }
    conn.close()
    return products

def save_products(self):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    for id, product in self.products.items():
        cursor.execute("UPDATE items SET quantity=? WHERE id=?", (product['quantity'], id))
    conn.commit()
    conn.close()

def display_products(self):
    self.products_list.clear()
    for id, product in self.products.items():
        item = QListWidgetItem(f"{product['id']}. {product['name']} - EG{product['price']:.2f} (Quantity: {product['quantity']})")
        self.products_list.addItem(item)

def add_to_cart(self):
    selected_item = self.products_list.currentItem()
    if selected_item:
        try:
            product_id = int(selected_item.text().split(".")[0])
            quantity, ok = QInputDialog.getInt(self, "Quantity", "Enter quantity:")
            if ok and quantity > 0:
                if self.products[product_id]['quantity'] >= quantity:
                    self.cart[product_id] = self.cart.get(product_id, 0) + quantity
                    self.products[product_id]['quantity'] -= quantity
                    self.cart_list.addItem(QListWidgetItem(f"{self.products[product_id]['name']} x {quantity}"))
                    self.display_products()
                else:
                    QMessageBox.warning(self, "Warning", f"Insufficient quantity for {self.products[product_id]['name']}. Only {self.products[product_id]['quantity']} available.")
            else:
                QMessageBox.warning(self, "Error", "Invalid quantity. Please enter a positive number.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Invalid ID. Please enter a number.")

def calculate_total(self):
    total = 0
    for product_id, quantity in self.cart.items():
        total += self.products[product_id]['price'] * quantity
    self.total_label.setText(f"Total: EG {total:.2f}")
    return total

def clear_cart(self):
    self.cart_list.clear()
    self.cart.clear()
    self.total_label.setText("Total: EG 0.00")

def checkout(self):
    total = self.calculate_total()

    if total > 0:
        payment_amount, ok = QInputDialog.getDouble(self, "Payment", "Enter payment amount:", decimals=2)
        if ok and payment_amount >= total:
            change = payment_amount - total
            QMessageBox.information(self, "Checkout", f"Thank you for your purchase! \nChange: EG {change:.2f}")
            self.save_sales(total, payment_amount)
            self.clear_cart()
            self.save_products()
            self.show_receipt(total, change)
        else:
            QMessageBox.warning(self, "Error", "Insufficient payment.")
    else:
        QMessageBox.information(self, "Checkout", "Cart is empty.")

def save_sales(self, total, payment_amount):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items_str = ', '.join(f"{self.products[product_id]['name']} x {quantity}" for product_id, quantity in self.cart.items())
    cursor.execute("INSERT INTO sales (timestamp, items, total) VALUES (?, ?, ?)", 
                  (timestamp, items_str, total))
    conn.commit()
    conn.close()

        
def search_by_id(self):
    search_id = self.id_search_entry.text()
    try:
        search_id = int(search_id)
        if search_id in self.products:
            self.products_list.clear()
            item = QListWidgetItem(f"{self.products[search_id]['id']}. {self.products[search_id]['name']} - EG{self.products[search_id]['price']:.2f} (Quantity: {self.products[search_id]['quantity']})")
            self.products_list.addItem(item)
        else:
            QMessageBox.information(self, "Search Result", "Product not found.")
    except ValueError:
        QMessageBox.warning(self, "Error", "Invalid ID. Please enter a number.")

def search_by_name(self):
    search_name = self.name_search_entry.text()
    found = False
    self.products_list.clear()
    for id, product in self.products.items():
        if search_name.lower() in product['name'].lower():
            item = QListWidgetItem(f"{product['id']}. {product['name']} - EG{product['price']:.2f} (Quantity: {product['quantity']})")
            self.products_list.addItem(item)
            found = True
    if not found:
        QMessageBox.information(self, "Search Result", "Product not found.")

# --- Main Window Setup ---

class CashierApp(QWidget):
    def __init__(self):
        super().__init__()

        create_database()
        self.products = load_products()
        self.cart = {}

        self.setWindowTitle("Cashier App")
        self.setWindowIcon(QIcon('cashier.png'))  # Replace with your icon file
        self.setStyleSheet("""
            QWidget {
                background-color: #F0F0F0;
                font-family: Arial;
            }
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #FFF;
            }
            QLabel {
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50; /* Green */
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #45a049; 
            }
            QListWidget {
                background-color: #FFF;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            QTableWidget {
                background-color: #FFF;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
        """)

        # --- UI Elements ---

        # Product List Frame
        products_frame = QFrame(self)
        products_frame.setFrameShape(QFrame.StyledPanel)
        products_frame.setFrameShadow(QFrame.Raised)

        products_label = QLabel("Available Products", products_frame)
        products_label.setFont(QFont("Arial", 12, QFont.Bold))
        products_label.setStyleSheet("color: #333")

        self.products_list = QListWidget(products_frame)  # Class attribute
        self.products_list.setFont(QFont("Arial", 10))
        self.display_products()

        products_layout = QVBoxLayout()
        products_layout.addWidget(products_label)
        products_layout.addWidget(self.products_list)
        products_frame.setLayout(products_layout)

        # Search Frame
        search_frame = QFrame(self)
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_frame.setFrameShadow(QFrame.Raised)

        search_label = QLabel("Search:", search_frame)
        search_label.setFont(QFont("Arial", 10, QFont.Bold))
        search_label.setStyleSheet("color: #333")

        id_search_label = QLabel("ID:", search_frame)
        id_search_label.setFont(QFont("Arial", 10))
        self.id_search_entry = QLineEdit(search_frame)  # Class attribute
        self.id_search_entry.setPlaceholderText("Enter Product ID")
        id_search_button = QPushButton("Search by ID", search_frame)
        id_search_button.clicked.connect(self.search_by_id)

        name_search_label = QLabel("Name:", search_frame)
        name_search_label.setFont(QFont("Arial", 10))
        self.name_search_entry = QLineEdit(search_frame)  # Class attribute
        self.name_search_entry.setPlaceholderText("Enter Product Name")
        name_search_button = QPushButton("Search by Name", search_frame)
        name_search_button.clicked.connect(self.search_by_name)

        search_layout = QHBoxLayout()
        search_layout.addWidget(search_label)
        search_layout.addSpacing(10)
        search_layout.addWidget(id_search_label)
        search_layout.addWidget(self.id_search_entry)
        search_layout.addWidget(id_search_button)
        search_layout.addSpacing(10)
        search_layout.addWidget(name_search_label)
        search_layout.addWidget(self.name_search_entry)
        search_layout.addWidget(name_search_button)
        search_frame.setLayout(search_layout)

        # Cart Frame
        cart_frame = QFrame(self)
        cart_frame.setFrameShape(QFrame.StyledPanel)
        cart_frame.setFrameShadow(QFrame.Raised)

        cart_label = QLabel("Your Cart", cart_frame)
        cart_label.setFont(QFont("Arial", 12, QFont.Bold))
        cart_label.setStyleSheet("color: #333")

        self.cart_list = QListWidget(cart_frame)  # Class attribute
        self.cart_list.setFont(QFont("Arial", 10))

        cart_layout = QVBoxLayout()
        cart_layout.addWidget(cart_label)
        cart_layout.addWidget(self.cart_list)
        cart_frame.setLayout(cart_layout)

        # Buttons Frame
        buttons_frame = QFrame(self)
        buttons_frame.setFrameShape(QFrame.StyledPanel)
        buttons_frame.setFrameShadow(QFrame.Raised)

        add_button = QPushButton("Add to Cart", buttons_frame)
        add_button.clicked.connect(self.add_to_cart)

        clear_button = QPushButton("Clear Cart", buttons_frame)
        clear_button.clicked.connect(self.clear_cart)

        checkout_button = QPushButton("Checkout", buttons_frame)
        checkout_button.clicked.connect(self.checkout)

        self.total_label = QLabel("Total: EG 0.00", buttons_frame)  # Class attribute
        self.total_label.setFont(QFont("Arial", 12, QFont.Bold))

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(clear_button)
        buttons_layout.addWidget(checkout_button)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.total_label)
        buttons_frame.setLayout(buttons_layout)

        # --- Layout ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(products_frame)
        main_layout.addWidget(search_frame)
        main_layout.addWidget(cart_frame)
        main_layout.addWidget(buttons_frame)
        self.setLayout(main_layout)

        # Add spacing between frames
        main_layout.setSpacing(10)

    # --- Slot Functions ---
    def search_by_id(self):
        search_by_id(self)

    def search_by_name(self):
        search_by_name(self)

    def add_to_cart(self):
        add_to_cart(self)

    def calculate_total(self):
        return calculate_total(self)

    def clear_cart(self):
        clear_cart(self)

    def checkout(self):
        checkout(self)

    def save_products(self):
        save_products(self)

    def display_products(self):
        display_products(self)

    def save_sales(self, total, payment_amount):
        save_sales(self, total, payment_amount)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    cashier_app = CashierApp()
    cashier_app.show()
    sys.exit(app.exec_())