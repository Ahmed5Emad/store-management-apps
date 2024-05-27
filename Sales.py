import sys
import datetime
import sqlite3
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, 
                             QComboBox, QListWidget, QListWidgetItem, QMessageBox, 
                             QGridLayout, QHBoxLayout, QFrame, QStyleFactory)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

DATABASE_PATH = "store.db"  # Path to your SQLite database

def create_database():
    """Creates the database table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
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

# --- Sales Data Functions ---
def load_sales_data():
    """Loads sales data from the database."""
    sales = []
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sales")
    for row in cursor.fetchall():
        sales.append({
            'id': row[0],
            'timestamp': datetime.datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S'),
            'items': row[2],
            'total': row[3]
        })
    conn.close()
    return sales

def display_sales_data(sales_listbox, sales, year, month, day):
    """Displays filtered sales data in the listbox."""
    sales_listbox.clear()  # Clear previous items

    filtered_sales = []
    for sale in sales:
        if year and sale['timestamp'].year != int(year):
            continue
        if month and sale['timestamp'].month != int(month):
            continue
        if day and sale['timestamp'].day != int(day):
            continue

        filtered_sales.append(sale)

    if not filtered_sales:
        QMessageBox.information(None, "Sales Analysis", "No sales data found for the selected period.")
        return

    for sale in filtered_sales:
        item = QListWidgetItem(f"{sale['timestamp'].strftime('%Y-%m-%d %H:%M:%S')} - {sale['items']} - EG {sale['total']:.2f}")
        sales_listbox.addItem(item)

def analyze_sales_data(sales, year, month, day):
    """Analyzes sales data and displays results in a message box."""
    if not sales:
        QMessageBox.information(None, "Sales Analysis", "No sales data found.")
        return

    filtered_sales = []
    for sale in sales:
        if year and sale['timestamp'].year != int(year):
            continue
        if month and sale['timestamp'].month != int(month):
            continue
        if day and sale['timestamp'].day != int(day):
            continue

        filtered_sales.append(sale)

    if not filtered_sales:
        QMessageBox.information(None, "Sales Analysis", "No sales data found for the selected period.")
        return

    total_sales = sum([sale['total'] for sale in filtered_sales])
    avg_sale = total_sales / len(filtered_sales) if filtered_sales else 0.0

    item_counts = {}
    for sale in filtered_sales:
        for item in sale['items'].split(', '):
            item_name, quantity = item.split(' x ')
            item_counts[item_name] = item_counts.get(item_name, 0) + int(quantity)

    results_str = f"Total Sales: EG {total_sales:.2f}\nAverage Sale: EG {avg_sale:.2f}\n\nSales per Item:\n"
    for item, count in item_counts.items():
        results_str += f"{item}: {count}\n"

    QMessageBox.information(None, "Sales Analysis", results_str)

# --- Main Window Class ---
class SalesDataAnalysis(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sales Data Analysis")

        # --- Apply a Modern Style ---
        # You can experiment with different styles:
        # 'Fusion', 'Windows', 'Macintosh', etc.
        QApplication.setStyle(QStyleFactory.create('Fusion'))

        create_database() 
        self.sales = load_sales_data() 
        self.initUI()

    def initUI(self):
        """Initializes the user interface."""

        # --- Font ---
        font = QFont()
        font.setFamily("Arial")  # Or your preferred font
        font.setPointSize(10)
        self.setFont(font)

        # --- Date Selection ---
        self.year_label = QLabel("Year:")
        self.year_combo = QComboBox(self)
        self.year_combo.addItems([str(x) for x in range(2023, 2041)])

        self.month_label = QLabel("Month:")
        self.month_combo = QComboBox(self)
        self.month_combo.addItems([str(x) for x in range(1, 13)])

        self.day_label = QLabel("Day:")
        self.day_combo = QComboBox(self)
        self.day_combo.addItems([str(x) for x in range(1, 32)])

        # --- Sales Data Listbox ---
        self.sales_listbox = QListWidget(self)
        self.sales_listbox.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #e6f2ff; 
                color: #000; 
            }
        """)

        # --- Buttons ---
        self.display_button = QPushButton("Display Sales Data")
        self.display_button.clicked.connect(self.on_display_clicked)

        self.analyze_button = QPushButton("Analyze Sales Data")
        self.analyze_button.clicked.connect(self.on_analyze_clicked)

        self.clear_button = QPushButton("Clear Date")
        self.clear_button.clicked.connect(self.on_clear_clicked)

        # --- Button Styling ---
        button_style = """
            QPushButton {
                background-color: #4CAF50; /* Green */
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 4px;
            }

            QPushButton:hover {
                background-color: #45a049; 
            }
        """
        self.display_button.setStyleSheet(button_style)
        self.analyze_button.setStyleSheet(button_style)
        self.clear_button.setStyleSheet(button_style)

        # --- Layout ---
        date_layout = QHBoxLayout()
        date_layout.addWidget(self.year_label)
        date_layout.addWidget(self.year_combo)
        date_layout.addWidget(self.month_label)
        date_layout.addWidget(self.month_combo)
        date_layout.addWidget(self.day_label)
        date_layout.addWidget(self.day_combo)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.display_button)
        button_layout.addWidget(self.analyze_button)
        button_layout.addWidget(self.clear_button)

        main_layout = QVBoxLayout()
        main_layout.addLayout(date_layout)
        main_layout.addWidget(self.sales_listbox)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    # --- Button Event Handlers ---
    def on_display_clicked(self):
        year = self.year_combo.currentText()
        month = self.month_combo.currentText()
        day = self.day_combo.currentText()
        display_sales_data(self.sales_listbox, self.sales, year, month, day)

    def on_analyze_clicked(self):
        year = self.year_combo.currentText()
        month = self.month_combo.currentText()
        day = self.day_combo.currentText()
        analyze_sales_data(self.sales, year, month, day)

    def on_clear_clicked(self):
        self.year_combo.setCurrentIndex(-1)  # Clear year selection
        self.month_combo.setCurrentIndex(-1)  # Clear month selection
        self.day_combo.setCurrentIndex(-1)  # Clear day selection
        self.sales_listbox.clear()  # Clear listbox

# --- Main Application ---
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SalesDataAnalysis()
    window.show()
    sys.exit(app.exec_())