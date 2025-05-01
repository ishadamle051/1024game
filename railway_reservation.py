import mysql.connector as connection
import bcrypt
import re
import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTextEdit, QDialog,
    QFormLayout, QMessageBox, QDateEdit, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import os

try:
    mydb = connection.connect(
        host="localhost",
        user="root",
        password="isha1108",
        database="railway_system",
        use_pure=True
    )
    cursor = mydb.cursor(dictionary=True)
    print("✅ Connected to MySQL: railway_system")
    
    cursor.execute("SHOW TABLES LIKE 'users'")
    if not cursor.fetchone():
        print("❌ Error: 'users' table does not exist in railway_system")
        sys.exit(1)
    print("✅ Verified: 'users' table exists")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)

def register_user(username, password, role="Normal"):
    if not all([username, password]):
        return "⚠ Username and password are required."
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
        return "⚠ Username must be 3-20 characters (letters, numbers, underscores)."
    if role not in ["Normal", "Admin"]:
        return "⚠ Invalid role. Must be 'Normal' or 'Admin'."
    
    try:
        query = "SELECT user_id FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        if cursor.fetchone():
            return "⚠ Username already exists."
        
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        query = "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, hashed_password.decode('utf-8'), role))
        mydb.commit()
        user_id = cursor.lastrowid
        return f"✅ User registered successfully. User ID: {user_id}"
    except Exception as e:
        mydb.rollback()
        return f"❌ Error during registration: {e}"

def login_user(username, password, role):
    try:
        query = "SELECT user_id, password, role FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        
        if not user or user['role'] != role:
            return None, "❌ Invalid username, password, or role."
        
        stored_password = user['password'].encode('utf-8')
        if not bcrypt.checkpw(password.encode('utf-8'), stored_password):
            return None, "❌ Invalid username, password, or role."
        
        return user['user_id'], f"✅ Welcome back, {username}!"
    except Exception as e:
        return None, f"❌ Error during login: {e}"

def get_trains():
    try:
        query = "SELECT train_id, train_name, train_type FROM trains"
        cursor.execute(query)
        trains = cursor.fetchall()
        if not trains:
            return "❌ No trains found."
        
        result = ""
        for train in trains:
            result += (
                f"Train ID   : {train['train_id']}\n"
                f"Name       : {train['train_name']}\n"
                f"Type       : {train['train_type']}\n"
                f"{'-'*40}\n"
            )
        return result
    except Exception as e:
        return f"❌ Error fetching trains: {e}"

def add_train(train_name, train_type):
    if not all([train_name, train_type]):
        return "⚠ Train name and type are required."
    if train_type not in ["Express", "Passenger", "Cargo"]:
        return "⚠ Invalid train type. Must be Express, Passenger, or Cargo."
    
    try:
        query = "INSERT INTO trains (train_name, train_type) VALUES (%s, %s)"
        cursor.execute(query, (train_name, train_type))
        mydb.commit()
        train_id = cursor.lastrowid
        return f"✅ Train added successfully. Train ID: {train_id}"
    except Exception as e:
        mydb.rollback()
        return f"❌ Error adding train: {e}"

def get_stations():
    try:
        query = "SELECT station_name FROM stations ORDER BY station_name"
        cursor.execute(query)
        stations = cursor.fetchall()
        return [station['station_name'] for station in stations]
    except Exception as e:
        return []

def search_trains(start_station, end_station, date=None):
    if not all([start_station, end_station]):
        return "⚠ Both 'from' and 'to' stations are required."
    
    try:
        query = """
            SELECT 
                ts.schedule_id,
                t.train_id,
                t.train_name,
                t.train_type,
                s1.station_name as start_station,
                s2.station_name as end_station,
                ts.departure_time,
                ts.arrival_time,
                COALESCE((
                    SELECT COUNT(*)
                    FROM seat_availability sa
                    JOIN seats s ON sa.seat_id = s.seat_id
                    WHERE sa.schedule_id = ts.schedule_id AND sa.available = TRUE
                ), 0) as available_seats
            FROM train_schedules ts
            JOIN train_routes tr ON ts.route_id = tr.route_id
            JOIN trains t ON tr.train_id = t.train_id
            JOIN stations s1 ON tr.start_station_id = s1.station_id
            JOIN stations s2 ON tr.end_station_id = s2.station_id
            WHERE s1.station_name = %s
            AND s2.station_name = %s
        """
        params = [start_station, end_station]
        
        if date:
            query += " AND DATE(ts.departure_time) = %s"
            params.append(date)
        
        cursor.execute(query, params)
        trains = cursor.fetchall()
        
        print(f"Debug: Found {len(trains)} trains for {start_station} to {end_station}")
        for train in trains:
            print(f"Debug: Schedule ID {train['schedule_id']}, Available Seats: {train['available_seats']}")
        
        if not trains:
            return "❌ No trains found for the specified route."
        
        result = ""
        for train in trains:
            result += (
                f"Schedule ID    : {train['schedule_id']}\n"
                f"Train ID       : {train['train_id']}\n"
                f"Train Name     : {train['train_name']}\n"
                f"Type           : {train['train_type']}\n"
                f"From           : {train['start_station']}\n"
                f"To             : {train['end_station']}\n"
                f"Departure      : {train['departure_time']}\n"
                f"Arrival        : {train['arrival_time']}\n"
                f"Available Seats: {train['available_seats']}\n"
                f"{'-'*50}\n"
            )
        return result
    except Exception as e:
        print(f"Debug: Error searching trains: {e}")
        return f"❌ Error searching trains: {e}"

def get_schedules():
    try:
        query = """
            SELECT 
                ts.schedule_id,
                t.train_name,
                s1.station_name as start_station,
                s2.station_name as end_station,
                ts.departure_time,
                ts.arrival_time,
                t.train_type
            FROM train_schedules ts
            JOIN train_routes tr ON ts.route_id = tr.route_id
            JOIN trains t ON tr.train_id = t.train_id
            JOIN stations s1 ON tr.start_station_id = s1.station_id
            JOIN stations s2 ON tr.end_station_id = s2.station_id
            ORDER BY ts.departure_time
        """
        cursor.execute(query)
        schedules = cursor.fetchall()
        
        if not schedules:
            return "❌ No schedules found."
        
        result = ""
        for schedule in schedules:
            result += (
                f"Schedule ID    : {schedule['schedule_id']}\n"
                f"Train Name     : {schedule['train_name']}\n"
                f"From           : {schedule['start_station']}\n"
                f"To             : {schedule['end_station']}\n"
                f"Departure      : {schedule['departure_time']}\n"
                f"Arrival        : {schedule['arrival_time']}\n"
                f"Type           : {schedule['train_type']}\n"
                f"{'-'*50}\n"
            )
        return result
    except Exception as e:
        return f"❌ Error fetching schedules: {e}"

def calculate_booking_amount(booking_id):
    try:
        query = """
            SELECT COUNT(p.passenger_id) as passenger_count
            FROM passengers p
            WHERE p.booking_id = %s
        """
        cursor.execute(query, (booking_id,))
        result = cursor.fetchone()
        passenger_count = result['passenger_count'] if result else 0
        amount = passenger_count * 50.0
        return amount
    except Exception as e:
        return 0.0

def get_available_seats(schedule_id):
    try:
        query = """
            SELECT s.seat_id, s.seat_number
            FROM seats s
            JOIN seat_availability sa ON s.seat_id = sa.seat_id
            WHERE sa.schedule_id = %s AND sa.available = TRUE
        """
        cursor.execute(query, (schedule_id,))
        seats = cursor.fetchall()
        print(f"Debug: Found {len(seats)} available seats for schedule_id {schedule_id}")
        return seats
    except Exception as e:
        print(f"Debug: Error fetching available seats: {e}")
        return []

def initialize_seat_availability(schedule_id, train_id):
    try:
        query = "SELECT seat_id FROM seats WHERE train_id = %s"
        cursor.execute(query, (train_id,))
        seats = cursor.fetchall()
        
        query = "INSERT INTO seat_availability (seat_id, schedule_id, available) VALUES (%s, %s, TRUE)"
        for seat in seats:
            cursor.execute(query, (seat['seat_id'], schedule_id))
        
        mydb.commit()
        print(f"✅ Initialized seat availability for schedule_id {schedule_id}")
    except Exception as e:
        mydb.rollback()
        print(f"❌ Error initializing seat availability: {e}")

def create_booking(user_id, schedule_id, passengers, start_station, end_station):
    try:
        query = """
            SELECT ts.schedule_id, t.train_name, ts.departure_time, ts.arrival_time
            FROM train_schedules ts
            JOIN train_routes tr ON ts.route_id = tr.route_id
            JOIN trains t ON tr.train_id = t.train_id
            JOIN stations s1 ON tr.start_station_id = s1.station_id
            JOIN stations s2 ON tr.end_station_id = s2.station_id
            WHERE ts.schedule_id = %s
            AND s1.station_name = %s
            AND s2.station_name = %s
        """
        cursor.execute(query, (schedule_id, start_station, end_station))
        schedule = cursor.fetchone()
        if not schedule:
            return "❌ Invalid schedule or stations.", None
        
        query = "INSERT INTO bookings (user_id, schedule_id, booking_date, status) VALUES (%s, %s, NOW(), 'Pending')"
        cursor.execute(query, (user_id, schedule_id))
        booking_id = cursor.lastrowid

        passenger_details = []
        for passenger in passengers:
            name = passenger['name']
            seat_id = passenger['seat_id']
            age = passenger['age']
            first_name = name.split()[0] if ' ' in name else name
            last_name = name.split()[1] if ' ' in name and len(name.split()) > 1 else ''
            query = "INSERT INTO passengers (passenger_name, first_name, last_name, age, seat_id, booking_id) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (name, first_name, last_name, age, seat_id, booking_id))

            query = "SELECT available FROM seat_availability WHERE seat_id = %s AND schedule_id = %s"
            cursor.execute(query, (seat_id, schedule_id))
            availability = cursor.fetchone()
            if not availability or not availability['available']:
                raise Exception(f"❌ Seat {seat_id} is not available for this schedule.")
            query = "UPDATE seat_availability SET available = FALSE WHERE seat_id = %s AND schedule_id = %s"
            cursor.execute(query, (seat_id, schedule_id))

            passenger_details.append({
                'name': name,
                'seat_id': seat_id,
                'age': age
            })

        mydb.commit()
        booking_details = {
            'booking_id': booking_id,
            'user_id': user_id,
            'schedule_id': schedule_id,
            'train_name': schedule['train_name'],
            'start_station': start_station,
            'end_station': end_station,
            'departure_time': schedule['departure_time'],
            'arrival_time': schedule['arrival_time'],
            'booking_date': datetime.now(),
            'passengers': passenger_details
        }
        return f"✅ Bookings created successfully. Booking ID: {booking_id}", booking_details
    except Exception as e:
        mydb.rollback()
        return f"❌ Error creating bookings: {e}", None

def process_payment(booking_id, amount):
    try:
        query = "INSERT INTO payment_transactions (booking_id, amount, payment_date, payment_status) VALUES (%s, %s, NOW(), 'Completed')"
        cursor.execute(query, (booking_id, amount))
        
        query = "UPDATE bookings SET status = 'Confirmed' WHERE booking_id = %s"
        cursor.execute(query, (booking_id,))
        
        mydb.commit()
        payment_id = cursor.lastrowid
        return f"✅ Payment processed successfully. Payment ID: {payment_id}"
    except Exception as e:
        mydb.rollback()
        return f"❌ Error processing payment: {e}"

def view_bookings(user_id, is_admin=False):
    try:
        if is_admin:
            query = """
                SELECT 
                    b.booking_id,
                    b.user_id,
                    b.schedule_id,
                    b.booking_date,
                    b.status,
                    t.train_name,
                    GROUP_CONCAT(p.passenger_name SEPARATOR ', ') as passengers,
                    GROUP_CONCAT(p.seat_id SEPARATOR ', ') as seat_ids
                FROM bookings b
                JOIN train_schedules ts ON b.schedule_id = ts.schedule_id
                JOIN train_routes tr ON ts.route_id = tr.route_id
                JOIN trains t ON tr.train_id = t.train_id
                LEFT JOIN passengers p ON b.booking_id = p.booking_id
                GROUP BY b.booking_id, b.user_id, b.schedule_id, b.booking_date, b.status, t.train_name
                ORDER BY b.booking_date DESC
            """
            params = []
        else:
            query = """
                SELECT 
                    b.booking_id,
                    b.user_id,
                    b.schedule_id,
                    b.booking_date,
                    b.status,
                    t.train_name,
                    GROUP_CONCAT(p.passenger_name SEPARATOR ', ') as passengers,
                    GROUP_CONCAT(p.seat_id SEPARATOR ', ') as seat_ids
                FROM bookings b
                JOIN train_schedules ts ON b.schedule_id = ts.schedule_id
                JOIN train_routes tr ON ts.route_id = tr.route_id
                JOIN trains t ON tr.train_id = t.train_id
                LEFT JOIN passengers p ON b.booking_id = p.booking_id
                WHERE b.user_id = %s
                GROUP BY b.booking_id, b.user_id, b.schedule_id, b.booking_date, b.status, t.train_name
                ORDER BY b.booking_date DESC
            """
            params = (user_id,)
        
        cursor.execute(query, params)
        bookings = cursor.fetchall()
        
        if not bookings:
            return "❌ No bookings found."
        
        result = ""
        for booking in bookings:
            result += (
                f"Booking ID    : {booking['booking_id']}\n"
                f"User ID       : {booking['user_id']}\n"
                f"Schedule ID   : {booking['schedule_id']}\n"
                f"Booking Date  : {booking['booking_date']}\n"
                f"Status        : {booking['status']}\n"
                f"Train Name    : {booking['train_name']}\n"
                f"Passengers    : {booking['passengers']}\n"
                f"Seat IDs      : {booking['seat_ids']}\n"
                f"{'-'*50}\n"
            )
        return result
    except Exception as e:
        return f"❌ Error viewing bookings: {e}"

def generate_booking_pdf(booking_details):
    filename = f"ticket_booking_{booking_details['booking_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Railway Booking Ticket", styles['Title']))
    elements.append(Spacer(1, 12))

    booking_info = [
        ["Booking ID:", str(booking_details['booking_id'])],
        ["User ID:", str(booking_details['user_id'])],
        ["Schedule ID:", str(booking_details['schedule_id'])],
        ["Train Name:", booking_details['train_name']],
        ["From Station:", booking_details['start_station']],
        ["To Station:", booking_details['end_station']],
        ["Departure Time:", str(booking_details['departure_time'])],
        ["Arrival Time:", str(booking_details['arrival_time'])],
        ["Booking Date:", str(booking_details['booking_date'].strftime('%Y-%m-%d %H:%M:%S'))],
    ]
    booking_table = Table(booking_info)
    booking_table.setStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ])
    elements.append(booking_table)
    elements.append(Spacer(1, 24))

    elements.append(Paragraph("Passenger Details", styles['Heading2']))
    passenger_data = [["Name", "Seat ID", "Age"]]
    for passenger in booking_details['passengers']:
        age = str(passenger['age']) if passenger['age'] is not None else "N/A"
        passenger_data.append([passenger['name'], passenger['seat_id'], age])
    passenger_table = Table(passenger_data)
    passenger_table.setStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 12),
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ])
    elements.append(passenger_table)
    elements.append(Spacer(1, 24))

    elements.append(Paragraph("Thank you for booking with Railway System!", styles['Normal']))

    doc.build(elements)
    return filename

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login")
        self.setFixedSize(300, 200)
        layout = QFormLayout(self)
        
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Normal", "Admin"])
        
        layout.addRow("Username:", self.username_input)
        layout.addRow("Password:", self.password_input)
        layout.addRow("Role:", self.role_combo)
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        layout.addRow(self.login_button)
        
        self.register_button = QPushButton("Register")
        self.register_button.clicked.connect(self.handle_register)
        layout.addRow(self.register_button)
    
    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.role_combo.currentText()
        
        user_id, message = login_user(username, password, role)
        if user_id:
            self.accept()
            QMessageBox.information(self, "Success", message)
            self.parent().set_user(user_id, role)
        else:
            QMessageBox.warning(self, "Error", message)
    
    def handle_register(self):
        username = self.username_input.text()
        password = self.password_input.text()
        role = self.role_combo.currentText()
        
        message = register_user(username, password, role)
        QMessageBox.information(self, "Registration", message)

class SearchTrainsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search Trains")
        self.setFixedSize(400, 400)
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        self.from_station = QComboBox()
        self.to_station = QComboBox()
        stations = get_stations()
        self.from_station.addItems(stations)
        self.to_station.addItems(stations)
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(datetime.now().date())
        
        form_layout.addRow("From:", self.from_station)
        form_layout.addRow("To:", self.to_station)
        form_layout.addRow("Date (optional):", self.date_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.handle_search)
        form_layout.addRow(self.search_button)
        
        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.result_area.setFont(QFont("Courier", 10))
        
        layout.addLayout(form_layout)
        layout.addWidget(QLabel("Results:"))
        layout.addWidget(self.result_area)
        
        self.book_button = QPushButton("Book Selected Train")
        self.book_button.clicked.connect(self.handle_book)
        layout.addWidget(self.book_button)
    
    def handle_search(self):
        start_station = self.from_station.currentText()
        end_station = self.to_station.currentText()
        date = self.date_input.date().toString("yyyy-MM-dd") if self.date_input.date() else None
        
        result = search_trains(start_station, end_station, date)
        self.result_area.setText(result)
    
    def handle_book(self):
        selected_text = self.result_area.toPlainText()
        if not selected_text:
            QMessageBox.warning(self, "Error", "Please search for trains first.")
            return
        
        import re
        schedule_id_match = re.search(r"Schedule ID\s*:\s*(\d+)", selected_text)
        if not schedule_id_match:
            QMessageBox.warning(self, "Error", "Please select a train schedule to book.")
            return
        
        schedule_id = int(schedule_id_match.group(1))
        start_station = self.from_station.currentText()
        end_station = self.to_station.currentText()
        
        dialog = BookingDialog(self, user_id=self.parent().user_id, schedule_id=schedule_id,
                             start_station=start_station, end_station=end_station)
        dialog.exec()

class AddTrainDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Train")
        self.setFixedSize(300, 200)
        layout = QFormLayout(self)
        
        self.train_name = QLineEdit()
        self.train_type = QComboBox()
        self.train_type.addItems(["Express", "Passenger", "Cargo"])
        
        layout.addRow("Train Name:", self.train_name)
        layout.addRow("Train Type:", self.train_type)
        
        self.add_button = QPushButton("Add Train")
        self.add_button.clicked.connect(self.handle_add)
        layout.addRow(self.add_button)
    
    def handle_add(self):
        train_name = self.train_name.text()
        train_type = self.train_type.currentText()
        
        message = add_train(train_name, train_type)
        QMessageBox.information(self, "Result", message)
        if "successfully" in message.lower():
            self.accept()

class PassengerDialog(QDialog):
    def __init__(self, parent=None, available_seats=None):
        super().__init__(parent)
        self.setWindowTitle("Add Passenger")
        self.setFixedSize(300, 200)
        self.available_seats = available_seats or []
        layout = QFormLayout(self)
        
        self.name_input = QLineEdit()
        self.age_input = QSpinBox()
        self.age_input.setRange(0, 120)
        self.seat_combo = QComboBox()
        self.seat_combo.addItems([f"{seat['seat_id']} ({seat['seat_number']})" for seat in self.available_seats])
        
        layout.addRow("Name:", self.name_input)
        layout.addRow("Age:", self.age_input)
        layout.addRow("Seat:", self.seat_combo)
        
        self.add_button = QPushButton("Add Passenger")
        self.add_button.clicked.connect(self.accept)
        layout.addRow(self.add_button)
    
    def get_passenger_details(self):
        seat_text = self.seat_combo.currentText()
        seat_id = int(seat_text.split()[0]) if seat_text else None
        return {
            'name': self.name_input.text(),
            'age': self.age_input.value(),
            'seat_id': seat_id
        }

class BookingDialog(QDialog):
    def __init__(self, parent=None, user_id=None, schedule_id=None, start_station=None, end_station=None):
        super().__init__(parent)
        self.setWindowTitle("Create Booking")
        self.setFixedSize(400, 400)
        self.user_id = user_id
        self.schedule_id = schedule_id
        self.start_station = start_station
        self.end_station = end_station
        self.passengers = []
        
        layout = QVBoxLayout(self)
        
        self.passenger_list = QTextEdit()
        self.passenger_list.setReadOnly(True)
        self.passenger_list.setFont(QFont("Courier", 10))
        
        self.add_passenger_button = QPushButton("Add Passenger")
        self.add_passenger_button.clicked.connect(self.add_passenger)
        
        self.confirm_button = QPushButton("Confirm Booking")
        self.confirm_button.clicked.connect(self.confirm_booking)
        
        layout.addWidget(QLabel("Passengers:"))
        layout.addWidget(self.passenger_list)
        layout.addWidget(self.add_passenger_button)
        layout.addWidget(self.confirm_button)
    
    def add_passenger(self):
        available_seats = get_available_seats(self.schedule_id)
        if not available_seats:
            QMessageBox.warning(self, "Error", "No available seats for this schedule.")
            return
        
        dialog = PassengerDialog(self, available_seats)
        if dialog.exec():
            passenger = dialog.get_passenger_details()
            if passenger['name'] and passenger['seat_id']:
                self.passengers.append(passenger)
                self.update_passenger_list()
                self.available_seats = [s for s in available_seats if s['seat_id'] != passenger['seat_id']]
    
    def update_passenger_list(self):
        text = ""
        for p in self.passengers:
            text += f"Name: {p['name']}, Age: {p['age']}, Seat ID: {p['seat_id']}\n"
        self.passenger_list.setText(text)
    
    def confirm_booking(self):
        if not self.passengers:
            QMessageBox.warning(self, "Error", "At least one passenger is required.")
            return
        
        message, booking_details = create_booking(
            self.user_id, self.schedule_id, self.passengers, self.start_station, self.end_station
        )
        if booking_details:
            amount = calculate_booking_amount(booking_details['booking_id'])
            payment_dialog = PaymentDialog(self, booking_details['booking_id'], amount)
            if payment_dialog.exec():
                payment_message = process_payment(booking_details['booking_id'], amount)
                if "successfully" in payment_message.lower():
                    try:
                        pdf_filename = generate_booking_pdf(booking_details)
                        QMessageBox.information(
                            self, "Success",
                            f"{message}\n{payment_message}\nPDF generated: {pdf_filename}"
                        )
                        self.accept()
                    except Exception as e:
                        QMessageBox.warning(self, "Error", f"Failed to generate PDF: {str(e)}")
                else:
                    QMessageBox.warning(self, "Error", payment_message)
            else:
                QMessageBox.warning(self, "Error", "Payment cancelled.")
        else:
            QMessageBox.warning(self, "Error", message)

class PaymentDialog(QDialog):
    def __init__(self, parent=None, booking_id=None, amount=None):
        super().__init__(parent)
        self.setWindowTitle("Payment Gateway")
        self.setFixedSize(300, 250)
        self.booking_id = booking_id
        self.amount = amount
        
        layout = QFormLayout(self)
        
        layout.addRow(QLabel(f"Booking ID: {booking_id}"))
        layout.addRow(QLabel(f"Amount: ${amount:.2f}"))
        
        self.card_number = QLineEdit()
        self.card_number.setPlaceholderText("1234 5678 9012 3456")
        self.expiry = QLineEdit()
        self.expiry.setPlaceholderText("MM/YY")
        self.cvv = QLineEdit()
        self.cvv.setPlaceholderText("123")
        self.cvv.setEchoMode(QLineEdit.EchoMode.Password)
        
        layout.addRow("Card Number:", self.card_number)
        layout.addRow("Expiry Date:", self.expiry)
        layout.addRow("CVV:", self.cvv)
        
        self.pay_button = QPushButton("Pay Now")
        self.pay_button.clicked.connect(self.handle_payment)
        layout.addRow(self.pay_button)
    
    def handle_payment(self):
        card_number = self.card_number.text().replace(" ", "")
        expiry = self.expiry.text()
        cvv = self.cvv.text()
        
        if not card_number or not expiry or not cvv:
            QMessageBox.warning(self, "Error", "All payment fields are required.")
            return
        if not re.match(r"^\d{16}$", card_number):
            QMessageBox.warning(self, "Error", "Invalid card number (must be 16 digits).")
            return
        if not re.match(r"^\d{2}/\d{2}$", expiry):
            QMessageBox.warning(self, "Error", "Invalid expiry date (MM/YY).")
            return
        if not re.match(r"^\d{3}$", cvv):
            QMessageBox.warning(self, "Error", "Invalid CVV (must be 3 digits).")
            return
        
        QMessageBox.information(self, "Success", "Payment validated (simulated).")
        self.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Railway Booking System")
        self.setMinimumSize(600, 400)
        self.user_id = None
        self.role = None
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        
        self.welcome_label = QLabel("Welcome to Railway Booking System")
        self.welcome_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.welcome_label)
        
        self.button_layout = QHBoxLayout()
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.show_login_dialog)
        self.button_layout.addWidget(self.login_button)
        
        self.layout.addLayout(self.button_layout)
        self.layout.addStretch()
    
    def set_user(self, user_id, role):
        self.user_id = user_id
        self.role = role
        self.welcome_label.setText(f"Welcome, {role} User (ID: {user_id})")
        
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if role == "Normal":
            self.add_normal_user_buttons()
        elif role == "Admin":
            self.add_admin_buttons()
    
    def add_normal_user_buttons(self):
        buttons = [
            ("Search Trains", self.show_search_trains),
            ("Book Ticket", self.show_book_ticket),
            ("Make Payment", self.show_payment),
            ("View Bookings", self.view_bookings),
            ("Logout", self.logout)
        ]
        for text, handler in buttons:
            button = QPushButton(text)
            button.clicked.connect(handler)
            self.button_layout.addWidget(button)
    
    def add_admin_buttons(self):
        buttons = [
            ("Add Train", self.show_add_train),
            ("View Trains", self.view_trains),
            ("View Schedules", self.view_schedules),
            ("View All Bookings", self.view_all_bookings),
            ("Logout", self.logout)
        ]
        for text, handler in buttons:
            button = QPushButton(text)
            button.clicked.connect(handler)
            self.button_layout.addWidget(button)
    
    def show_login_dialog(self):
        dialog = LoginDialog(self)
        dialog.exec()
    
    def show_search_trains(self):
        dialog = SearchTrainsDialog(self)
        dialog.exec()
    
    def show_book_ticket(self):
        dialog = SearchTrainsDialog(self)
        dialog.exec()
    
    def show_payment(self):
        booking_id, ok = QLineEditDialog.getText(self, "Enter Booking ID", "Booking ID:")
        if ok and booking_id:
            try:
                booking_id = int(booking_id)
                amount = calculate_booking_amount(booking_id)
                if amount == 0:
                    QMessageBox.warning(self, "Error", "Invalid booking ID or no passengers found.")
                    return
                payment_dialog = PaymentDialog(self, booking_id, amount)
                if payment_dialog.exec():
                    payment_message = process_payment(booking_id, amount)
                    QMessageBox.information(self, "Result", payment_message)
            except ValueError:
                QMessageBox.warning(self, "Error", "Booking ID must be a number.")
    
    def show_add_train(self):
        dialog = AddTrainDialog(self)
        dialog.exec()
    
    def view_trains(self):
        result = get_trains()
        QMessageBox.information(self, "Trains", result)
    
    def view_schedules(self):
        result = get_schedules()
        QMessageBox.information(self, "Schedules", result)
    
    def view_bookings(self):
        result = view_bookings(self.user_id, is_admin=False)
        QMessageBox.information(self, "My Bookings", result)
    
    def view_all_bookings(self):
        result = view_bookings(self.user_id, is_admin=True)
        QMessageBox.information(self, "All Bookings", result)
    
    def logout(self):
        self.user_id = None
        self.role = None
        self.welcome_label.setText("Welcome to Railway Booking System")
        
        while self.button_layout.count():
            item = self.button_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.show_login_dialog)
        self.button_layout.addWidget(self.login_button)

class QLineEditDialog(QDialog):
    def __init__(self, parent=None, title="", label=""):
        super().__init__(parent)
        self.setWindowTitle(title)
        layout = QFormLayout(self)
        self.input = QLineEdit()
        layout.addRow(label, self.input)
        self.ok_button = QPushButton("OK")
        self.ok_button.clicked.connect(self.accept)
        layout.addRow(self.ok_button)
    
    @staticmethod
    def getText(parent, title, label):
        dialog = QLineEditDialog(parent, title, label)
        result = dialog.exec()
        return dialog.input.text(), result == QDialog.DialogCode.Accepted

class RailwayApp(QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.main_window = MainWindow()
        self.main_window.show()

if __name__ == "__main__":
    app = RailwayApp(sys.argv)
    sys.exit(app.exec())