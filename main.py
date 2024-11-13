from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit, QStackedWidget, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
import sys
import psycopg2
from fpdf import FPDF

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Мастер пол")
        
        self.setWindowIcon(QIcon("icon.ico"))

        self.setGeometry(100, 100, 800, 600)

         # Database connection
        self.connection = self.connect_to_db()
        
        # Set main background color
        self.setStyleSheet("background-color: #DECFB4;")
        
        # Main layout with horizontal layout for sidebar and content
        self.main_layout = QHBoxLayout()
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        # Sidebar layout for navigation buttons
        self.sidebar_layout = QVBoxLayout()

        logo_label = QLabel()
        logo_pixmap = QPixmap("logo.png")
        logo_label.setPixmap(logo_pixmap.scaledToWidth(150, Qt.SmoothTransformation))  # Устанавливаем ширину логотипа
        logo_label.setAlignment(Qt.AlignCenter)  # Центрируем логотип
        self.sidebar_layout.addWidget(logo_label)

        self.partners_button = QPushButton("Партнеры")
        self.partners_button.setStyleSheet("background-color: #DECFB4; color: #000000; font-weight: bold;")
        self.partners_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        self.sidebar_layout.addWidget(self.partners_button)
        
        self.history_button = QPushButton("История")
        self.history_button.setStyleSheet("background-color: #DECFB4; color: #000000; font-weight: bold;")
        self.history_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(1))
        self.sidebar_layout.addWidget(self.history_button)
        
        self.sidebar_layout.addStretch()  # Push buttons to the top
        
        self.main_layout.addLayout(self.sidebar_layout)
        
        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.main_layout.addWidget(self.stacked_widget)

        # Create pages
        self.create_partners_page()
        self.create_history_page()
        self.create_partner_form_page()

    def create_partners_page(self):
        # Partners Page
        partners_page = QWidget()
        partners_layout = QVBoxLayout()
        partners_page.setLayout(partners_layout)
        
        # Header layout for title and action buttons
        header_layout = QHBoxLayout()
        
        title = QLabel("Партнеры")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000;")
        header_layout.addWidget(title)

        # Add/Edit buttons
        add_button = QPushButton("+")
        add_button.setStyleSheet("background-color: #67BA80; color: #FFFFFF; font-weight: bold; font-size: 16px;")
        add_button.clicked.connect(lambda: self.open_partner_form("Добавление партнера"))
        header_layout.addWidget(add_button)

        edit_button = QPushButton("Редактировать")
        edit_button.setStyleSheet("background-color: #DECFB4; color: #000000; font-weight: bold;")
        edit_button.clicked.connect(self.open_edit_partner_form)
        header_layout.addWidget(edit_button)

        header_layout.addStretch()  # Push buttons to the right
        partners_layout.addLayout(header_layout)
        
        # Table for partners
        self.partners_table = QTableWidget(0, 6)  # Initially set to 0 rows, 6 columns
        self.partners_table.setHorizontalHeaderLabels(
            ["Наименование", "Тип", "Директор", "Номер телефона", "Рейтинг", "Скидка"]
        )
        self.partners_table.setStyleSheet("background-color: #FFFFFF; color: #000000;")
        self.partners_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only
        partners_layout.addWidget(self.partners_table)

        # Load data from database
        self.load_partners_data()

        self.stacked_widget.addWidget(partners_page)

    def create_partner_form_page(self):
        # Partner Form Page
        self.partner_form_page = QWidget()
        form_layout = QVBoxLayout()
        self.partner_form_page.setLayout(form_layout)

        self.form_title = QLabel()
        self.form_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #000000;")
        form_layout.addWidget(self.form_title)

        # Form fields
        self.form_inputs = {}
        fields = ["Наименование", "Директор", "Телефон", "Рейтинг", "Скидка"]
        for field in fields:
            label = QLabel(field)
            label.setStyleSheet("color: #000000;")
            input_field = QLineEdit()
            input_field.setStyleSheet("background-color: #F4E8D3; color: #000000;")
            self.form_inputs[field] = input_field
            form_layout.addWidget(label)
            form_layout.addWidget(input_field)

        # Dropdown for CompanyType
        self.type_dropdown = QComboBox()
        self.type_dropdown.setStyleSheet("background-color: #F4E8D3; color: #000000;")
        self.load_company_types()
        form_layout.addWidget(QLabel("Тип"))
        form_layout.addWidget(self.type_dropdown)

        # Submit button
        submit_button = QPushButton("Сохранить")
        submit_button.setStyleSheet("background-color: #67BA80; color: #FFFFFF; font-weight: bold;")
        submit_button.clicked.connect(self.save_partner)
        form_layout.addWidget(submit_button)

        # Back button
        back_button = QPushButton("Назад")
        back_button.setStyleSheet("background-color: #DECFB4; color: #000000; font-weight: bold;")
        back_button.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))
        form_layout.addWidget(back_button)

        self.stacked_widget.addWidget(self.partner_form_page)

    def open_partner_form(self, title_text, partner_data=None):
        # Update form title and fields for adding or editing
        self.form_title.setText(title_text)
        for i, (field, input_field) in enumerate(self.form_inputs.items()):
            input_field.setText(partner_data[i] if partner_data else "")
        
        # Show the partner form page
        self.stacked_widget.setCurrentWidget(self.partner_form_page)

    def save_partner(self):
        # Сбор данных из формы
        name = self.form_inputs["Наименование"].text()
        director = self.form_inputs["Директор"].text()
        phone = self.form_inputs["Телефон"].text()
        rating_str = self.form_inputs["Рейтинг"].text()
        
        # Преобразуем строку в число для rating, если это возможно
        try:
            rating = float(rating_str)  # Преобразуем в число с плавающей запятой
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Рейтинг должен быть числом.")
            return
        
        # Получаем тип партнера из выпадающего списка (если есть)
        type_id = self.type_dropdown.currentData()
        if not name or not director or not phone or not rating or not type_id:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, заполните все поля.")
            return

        cursor = self.connection.cursor()
        
        # Вычисляем скидку на основе проданных товаров
        discount = self.calculate_discount(self.edited_partner_id if hasattr(self, 'edited_partner_id') else 0)
        
        # Если это редактирование, то обновляем данные
        if hasattr(self, 'edited_partner_id'):
            query = """
            UPDATE Partners
            SET company_name = %s, type_partner = %s, director_full_name = %s, phone = %s, rating = %s, discount = %s
            WHERE id = %s;
            """
            cursor.execute(query, (name, type_id, director, phone, rating, discount, self.edited_partner_id))
            del self.edited_partner_id  # Очистим переменную после обновления
        else:
            # Если добавляем нового партнера
            query = """
            INSERT INTO Partners (company_name, type_partner, director_full_name, phone, rating, discount)
            VALUES (%s, %s, %s, %s, %s, %s);
            """
            cursor.execute(query, (name, type_id, director, phone, rating, discount))
        
        self.connection.commit()
        cursor.close()
        QMessageBox.information(self, "Успех", "Партнер успешно сохранен.")
        self.load_partners_data()
        self.load_history_data()

    def load_company_types(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, name FROM TypeCompany")
        types = cursor.fetchall()
        for type_id, type_name in types:
            self.type_dropdown.addItem(type_name, type_id)
        cursor.close()

    def connect_to_db(self):
        try:
            connection = psycopg2.connect(
                dbname="master_pol_db",
                user="master_pol",
                password="123456789",
                host="localhost",
                port="5432"
            )
            print("Connected to the database.")
            return connection
        except psycopg2.Error as e:
            QMessageBox.critical(self, "Database Error", f"Could not connect to the database.\nError: {e}")
            return None

    def load_partners_data(self):
        if self.connection:
            cursor = self.connection.cursor()
            # SQL запрос с LEFT JOIN для получения данных
            query = """
            SELECT p.company_name, pt.name AS type, p.director_full_name, p.phone, p.rating, p.discount
            FROM Partners p
            LEFT JOIN TypeCompany pt ON p.type_partner = pt.id;
            """
            cursor.execute(query)
            rows = cursor.fetchall()
            # Устанавливаем количество строк в таблице
            self.partners_table.setRowCount(len(rows))
            # Заполняем таблицу данными
            for row_num, row_data in enumerate(rows):
                for col_num, data in enumerate(row_data):
                    # Если это колонка скидки, добавляем символ '%'
                    if col_num == 5:  # Колонка скидки
                        data = f"{data}%" if data is not None else ""
                    self.partners_table.setItem(row_num, col_num, QTableWidgetItem(str(data) if data is not None else ''))
            cursor.close()

    def open_edit_partner_form(self):
        # Получаем выбранную строку в таблице
        selected_row = self.partners_table.currentRow()

        if selected_row == -1:
            QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите партнера для редактирования.")
            return

        # Извлекаем данные выбранного партнера
        name = self.partners_table.item(selected_row, 0).text() if self.partners_table.item(selected_row, 0) else ""
        type_name = self.partners_table.item(selected_row, 1).text() if self.partners_table.item(selected_row, 1) else ""
        director = self.partners_table.item(selected_row, 2).text() if self.partners_table.item(selected_row, 2) else ""
        phone = self.partners_table.item(selected_row, 3).text() if self.partners_table.item(selected_row, 3) else ""
        rating = self.partners_table.item(selected_row, 4).text() if self.partners_table.item(selected_row, 4) else ""
        discount = ""

        # Получаем id типа партнера
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM TypeCompany WHERE name = %s", (type_name,))
        type_id = cursor.fetchone()[0]
        cursor.close()

        # Открываем форму для редактирования и заполняем поля
        self.open_partner_form("Редактирование партнера", [name, director, phone, rating, discount])

        # Устанавливаем выбранный тип партнера
        index = self.type_dropdown.findData(type_id)
        if index != -1:
            self.type_dropdown.setCurrentIndex(index)

        # Сохраняем ID партнера, чтобы обновить его в базе данных
        self.edited_partner_id = self.get_partner_id(name, director)

    def get_partner_id(self, name, director):
        # Ищем id партнера по наименованию и директору (можно уточнить по другим полям)
        cursor = self.connection.cursor()
        cursor.execute("SELECT id FROM Partners WHERE company_name = %s AND director_full_name = %s", (name, director))
        partner_id = cursor.fetchone()[0]
        cursor.close()
        return partner_id
    
    def create_history_page(self):
        if not self.connection:
            print("No connection to the database.")
            return

        # History Page
        history_page = QWidget()
        history_layout = QVBoxLayout()
        history_page.setLayout(history_layout)
        
        title = QLabel("История")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #000000;")
        history_layout.addWidget(title)

        # Table for history
        self.history_table = QTableWidget(10, 4)  # 10 rows, 4 columns
        self.history_table.setHorizontalHeaderLabels(
            ["Продукция", "Количество продукта", "Наименование партнера", "Дата продажи"]
        )
        self.history_table.setStyleSheet("background-color: #FFFFFF; color: #000000;")
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only
        history_layout.addWidget(self.history_table)

        # Кнопка для экспорта в PDF
        export_button = QPushButton("Экспорт в PDF")
        export_button.setStyleSheet("background-color: #67BA80; color: #FFFFFF; font-weight: bold;")
        export_button.clicked.connect(self.export_history_to_pdf)
        history_layout.addWidget(export_button)

        # Load data after setting up the table
        self.load_history_data()

        self.stacked_widget.addWidget(history_page)

    def export_history_to_pdf(self):
        pdf = FPDF()
        pdf.add_page()

        # Подключение шрифта с поддержкой кириллицы
        pdf.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        pdf.set_font("DejaVu", size=11)

        # Заголовок документа
        pdf.cell(200, 10, txt="История продаж", ln=True, align="C")

        # Заголовки таблицы
        headers = ["Продукция", "Количество продукта", "Наименование партнера", "Дата продажи"]
        for header in headers:
            pdf.cell(50, 10, txt=header, border=1, align="C")
        pdf.ln()

        # Данные таблицы
        row_count = self.history_table.rowCount()
        column_count = self.history_table.columnCount()
        
        for row in range(row_count):
            for col in range(column_count):
                cell_text = self.history_table.item(row, col).text() if self.history_table.item(row, col) else ""
                pdf.cell(50, 10, txt=cell_text, border=1, align="C")
            pdf.ln()

        # Сохранение PDF
        pdf.output("history_report.pdf")
        QMessageBox.information(self, "Экспорт завершен", "История успешно экспортирована в PDF.")

    def load_history_data(self):
        if self.connection:
            cursor = self.connection.cursor()

            # SQL запрос для загрузки данных истории
            query = """
           SELECT 
                p.description AS "Продукция", 
                pp.quantity AS "Количество", 
                pr.company_name AS "Наименование партнера", 
                pp.date_of_sale AS "Дата продажи"
            FROM 
                PartnerProduct pp
            LEFT JOIN 
                Products p ON pp.id_product = p.id
            LEFT JOIN 
                Partners pr ON pp.id_partner = pr.id
            ORDER BY 
                pp.date_of_sale DESC;
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()

            # Устанавливаем количество строк в таблице
            self.history_table.setRowCount(len(rows))

            # Заполняем таблицу данными
            for row_num, row_data in enumerate(rows):
                for col_num, data in enumerate(row_data):
                    self.history_table.setItem(row_num, col_num, QTableWidgetItem(str(data) if data is not None else ''))

            cursor.close()

    def calculate_discount(self, partner_id):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT SUM(pp.quantity)
            FROM PartnerProduct pp
            WHERE pp.id_partner = %s
        """, (partner_id,))
        total_quantity = cursor.fetchone()[0] or 0  # Получаем общее количество проданных товаров
        cursor.close()

        # Логика для вычисления скидки
        if total_quantity <= 10000:
            return 0
        elif total_quantity <= 50000:
            return 5
        elif total_quantity <= 300000:
            return 10
        else:
            return 15
        
app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()
