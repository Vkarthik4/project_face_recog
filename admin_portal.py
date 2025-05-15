<<<<<<< HEAD
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QFormLayout, QComboBox, QDialog, QDialogButtonBox, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtCore import Qt
import csv
import os
import db_manager
import period_config
from student_portal import StudentPortal


class TimetableDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Subject")
        layout = QVBoxLayout()
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Enter Subject")
        layout.addWidget(self.subject_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_subject(self):
        return self.subject_input.text()


class PeriodHeaderDialog(QDialog):
    def __init__(self, current_text):
        super().__init__()
        self.setWindowTitle("Edit Period Time")
        layout = QVBoxLayout()
        self.time_input = QLineEdit(current_text)
        layout.addWidget(self.time_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_time_range(self):
        return self.time_input.text()


class AdminDashboard(QWidget):
    def __init__(self, login_screen=None):
        super().__init__()
        self.login_screen = login_screen
        self.setWindowTitle("Admin Dashboard")
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_timetable_tab(), "Assign Timetable")
        self.tabs.addTab(self.create_student_tab(), "Assign Students")
        self.tabs.addTab(self.create_attendance_tab(), "Attendance Log")

        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        
        # Set cursor to pointing hand when hovering over logout button
        logout_btn.setCursor(Qt.PointingHandCursor)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("🧑‍💼 Admin Panel"))
        top_layout.addStretch()
        top_layout.addWidget(logout_btn)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def logout(self):
        self.close()
        if self.login_screen:
            self.login_screen.show()

    def create_timetable_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.timetable = QTableWidget(5, 6)
        self.timetable.setVerticalHeaderLabels(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

        self.load_period_headers()
        self.timetable.cellDoubleClicked.connect(self.edit_cell)
        self.timetable.horizontalHeader().sectionDoubleClicked.connect(self.edit_period_header)

        layout.addWidget(self.timetable)

        finalize_btn = QPushButton("Finalize Timetable")
        finalize_btn.clicked.connect(self.finalize_timetable)
        
        # Set cursor to pointing hand when hovering over finalize button
        finalize_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(finalize_btn)

        tab.setLayout(layout)
        return tab

    def load_period_headers(self):
        headers = period_config.get_period_headers()
        self.timetable.setHorizontalHeaderLabels(headers)

    def edit_period_header(self, index):
        current_text = self.timetable.horizontalHeaderItem(index).text()
        dialog = PeriodHeaderDialog(current_text)
        if dialog.exec_() == QDialog.Accepted:
            new_text = dialog.get_time_range()
            self.timetable.setHorizontalHeaderItem(index, QTableWidgetItem(new_text))
            headers = [self.timetable.horizontalHeaderItem(i).text() for i in range(self.timetable.columnCount())]
            period_config.save_period_headers(headers)

    def edit_cell(self, row, col):
        dialog = TimetableDialog()
        if dialog.exec_() == QDialog.Accepted:
            subject = dialog.get_subject()
            item = QTableWidgetItem(subject)
            item.setBackground(QColor(173, 216, 230))
            self.timetable.setItem(row, col, item)

    def finalize_timetable(self):
        data = [["" for _ in range(6)] for _ in range(5)]
        for row in range(5):
            for col in range(6):
                item = self.timetable.item(row, col)
                if item:
                    data[row][col] = item.text()
        db_manager.save_timetable(data)
        print("✅ Timetable finalized and saved.")

    def create_student_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.student_table = QTableWidget()
        self.student_table.setColumnCount(5)
        self.student_table.setHorizontalHeaderLabels(["First Name", "Last Name", "Email", "Phone", "Password"])
        self.student_table.cellClicked.connect(self.populate_student_form)
        self.load_student_data()

        layout.addWidget(self.student_table)

        form = QFormLayout()
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.password_input = QLineEdit()

        self.class_combo = QComboBox()
        self.class_combo.addItems(["Section A", "Section B", "Section C"])
        self.reg_no_input = QLineEdit()

        form.addRow("First Name:", self.first_name_input)
        form.addRow("Last Name:", self.last_name_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Password:", self.password_input)
        form.addRow("Assign Class:", self.class_combo)
        form.addRow("Assign Reg. Number:", self.reg_no_input)

        assign_btn = QPushButton("Assign Registration Number")
        assign_btn.clicked.connect(self.assign_selected_student)
        
        # Set cursor to pointing hand when hovering over assign button
        assign_btn.setCursor(Qt.PointingHandCursor)

        view_attendance_btn = QPushButton("View Student Attendance")
        view_attendance_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        
        # Set cursor to pointing hand when hovering over view attendance button
        view_attendance_btn.setCursor(Qt.PointingHandCursor)

        layout.addLayout(form)
        layout.addWidget(assign_btn)
        layout.addWidget(view_attendance_btn)

        tab.setLayout(layout)
        return tab

    def load_student_data(self):
        students = db_manager.load_students()
        self.student_table.setRowCount(len(students))
        for row, (email, info) in enumerate(students.items()):
            self.student_table.setItem(row, 0, QTableWidgetItem(info.get("first_name", "")))
            self.student_table.setItem(row, 1, QTableWidgetItem(info.get("last_name", "")))
            self.student_table.setItem(row, 2, QTableWidgetItem(email))
            self.student_table.setItem(row, 3, QTableWidgetItem(info.get("phone", "")))
            self.student_table.setItem(row, 4, QTableWidgetItem(info.get("password", "")))

    def populate_student_form(self, row, column):
        self.first_name_input.setText(self.student_table.item(row, 0).text())
        self.last_name_input.setText(self.student_table.item(row, 1).text())
        self.email_input.setText(self.student_table.item(row, 2).text())
        self.phone_input.setText(self.student_table.item(row, 3).text())
        self.password_input.setText(self.student_table.item(row, 4).text())
        self.reg_no_input.setText(f"REG-{row+1:03d}")

    def assign_selected_student(self):
        email = self.email_input.text()
        section = self.class_combo.currentText()
        reg_no = self.reg_no_input.text()

        students = db_manager.load_students()
        if email in students:
            students[email]["section"] = section
            students[email]["reg_no"] = reg_no
            db_manager.save_students(students)
            QMessageBox.information(self, "Success", f"{email} assigned to {section} with Reg No: {reg_no}")
        else:
            QMessageBox.warning(self, "Error", "Student record not found.")

    def create_attendance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)
        self.attendance_table.setHorizontalHeaderLabels(["Name", "Reg No", "Period", "Status"])
        self.load_attendance_data()

        layout.addWidget(self.attendance_table)
        tab.setLayout(layout)
        return tab

    def load_attendance_data(self):
        path = "data/attendance_logs.csv"
        if not os.path.exists(path):
            return
        with open(path, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.attendance_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j in range(len(row)):
                    item = QTableWidgetItem(row[j])
                    if row[3].lower() == "present":
                        item.setIcon(QIcon.fromTheme("dialog-apply"))
                    self.attendance_table.setItem(i, j, item)


class AdminLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.resize(300, 150)

        layout = QVBoxLayout()
        self.label = QLabel("Login Portal")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        
        # Set cursor to pointing hand when hovering over the login button
        self.login_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.label)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)

    def login(self):
        user = self.username.text()
        pwd = self.password.text()
        if user == "admin" and pwd == "admin":
            self.hide()
            self.dashboard = AdminDashboard(login_screen=self)
            self.dashboard.show()
        elif user == "student" and pwd == "student":
            self.hide()
            self.portal = StudentPortal()
            self.portal.show()
        else:
            self.label.setText("Invalid Credentials")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = AdminLogin()
    login.show()
    sys.exit(app.exec_())
=======
import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QTabWidget, QTableWidget, QTableWidgetItem,
    QFormLayout, QComboBox, QDialog, QDialogButtonBox, QMessageBox, QHBoxLayout
)
from PyQt5.QtGui import QColor, QIcon
from PyQt5.QtCore import Qt
import csv
import os
import db_manager
import period_config
from student_portal import StudentPortal


class TimetableDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter Subject")
        layout = QVBoxLayout()
        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Enter Subject")
        layout.addWidget(self.subject_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_subject(self):
        return self.subject_input.text()


class PeriodHeaderDialog(QDialog):
    def __init__(self, current_text):
        super().__init__()
        self.setWindowTitle("Edit Period Time")
        layout = QVBoxLayout()
        self.time_input = QLineEdit(current_text)
        layout.addWidget(self.time_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_time_range(self):
        return self.time_input.text()


class AdminDashboard(QWidget):
    def __init__(self, login_screen=None):
        super().__init__()
        self.login_screen = login_screen
        self.setWindowTitle("Admin Dashboard")
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_timetable_tab(), "Assign Timetable")
        self.tabs.addTab(self.create_student_tab(), "Assign Students")
        self.tabs.addTab(self.create_attendance_tab(), "Attendance Log")

        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout)
        
        # Set cursor to pointing hand when hovering over logout button
        logout_btn.setCursor(Qt.PointingHandCursor)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("🧑‍💼 Admin Panel"))
        top_layout.addStretch()
        top_layout.addWidget(logout_btn)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def logout(self):
        self.close()
        if self.login_screen:
            self.login_screen.show()

    def create_timetable_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.timetable = QTableWidget(5, 6)
        self.timetable.setVerticalHeaderLabels(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

        self.load_period_headers()
        self.timetable.cellDoubleClicked.connect(self.edit_cell)
        self.timetable.horizontalHeader().sectionDoubleClicked.connect(self.edit_period_header)

        layout.addWidget(self.timetable)

        finalize_btn = QPushButton("Finalize Timetable")
        finalize_btn.clicked.connect(self.finalize_timetable)
        
        # Set cursor to pointing hand when hovering over finalize button
        finalize_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(finalize_btn)

        tab.setLayout(layout)
        return tab

    def load_period_headers(self):
        headers = period_config.get_period_headers()
        self.timetable.setHorizontalHeaderLabels(headers)

    def edit_period_header(self, index):
        current_text = self.timetable.horizontalHeaderItem(index).text()
        dialog = PeriodHeaderDialog(current_text)
        if dialog.exec_() == QDialog.Accepted:
            new_text = dialog.get_time_range()
            self.timetable.setHorizontalHeaderItem(index, QTableWidgetItem(new_text))
            headers = [self.timetable.horizontalHeaderItem(i).text() for i in range(self.timetable.columnCount())]
            period_config.save_period_headers(headers)

    def edit_cell(self, row, col):
        dialog = TimetableDialog()
        if dialog.exec_() == QDialog.Accepted:
            subject = dialog.get_subject()
            item = QTableWidgetItem(subject)
            item.setBackground(QColor(173, 216, 230))
            self.timetable.setItem(row, col, item)

    def finalize_timetable(self):
        data = [["" for _ in range(6)] for _ in range(5)]
        for row in range(5):
            for col in range(6):
                item = self.timetable.item(row, col)
                if item:
                    data[row][col] = item.text()
        db_manager.save_timetable(data)
        print("✅ Timetable finalized and saved.")

    def create_student_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.student_table = QTableWidget()
        self.student_table.setColumnCount(5)
        self.student_table.setHorizontalHeaderLabels(["First Name", "Last Name", "Email", "Phone", "Password"])
        self.student_table.cellClicked.connect(self.populate_student_form)
        self.load_student_data()

        layout.addWidget(self.student_table)

        form = QFormLayout()
        self.first_name_input = QLineEdit()
        self.last_name_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.password_input = QLineEdit()

        self.class_combo = QComboBox()
        self.class_combo.addItems(["Section A", "Section B", "Section C"])
        self.reg_no_input = QLineEdit()

        form.addRow("First Name:", self.first_name_input)
        form.addRow("Last Name:", self.last_name_input)
        form.addRow("Email:", self.email_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Password:", self.password_input)
        form.addRow("Assign Class:", self.class_combo)
        form.addRow("Assign Reg. Number:", self.reg_no_input)

        assign_btn = QPushButton("Assign Registration Number")
        assign_btn.clicked.connect(self.assign_selected_student)
        
        # Set cursor to pointing hand when hovering over assign button
        assign_btn.setCursor(Qt.PointingHandCursor)

        view_attendance_btn = QPushButton("View Student Attendance")
        view_attendance_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(2))
        
        # Set cursor to pointing hand when hovering over view attendance button
        view_attendance_btn.setCursor(Qt.PointingHandCursor)

        layout.addLayout(form)
        layout.addWidget(assign_btn)
        layout.addWidget(view_attendance_btn)

        tab.setLayout(layout)
        return tab

    def load_student_data(self):
        students = db_manager.load_students()
        self.student_table.setRowCount(len(students))
        for row, (email, info) in enumerate(students.items()):
            self.student_table.setItem(row, 0, QTableWidgetItem(info.get("first_name", "")))
            self.student_table.setItem(row, 1, QTableWidgetItem(info.get("last_name", "")))
            self.student_table.setItem(row, 2, QTableWidgetItem(email))
            self.student_table.setItem(row, 3, QTableWidgetItem(info.get("phone", "")))
            self.student_table.setItem(row, 4, QTableWidgetItem(info.get("password", "")))

    def populate_student_form(self, row, column):
        self.first_name_input.setText(self.student_table.item(row, 0).text())
        self.last_name_input.setText(self.student_table.item(row, 1).text())
        self.email_input.setText(self.student_table.item(row, 2).text())
        self.phone_input.setText(self.student_table.item(row, 3).text())
        self.password_input.setText(self.student_table.item(row, 4).text())
        self.reg_no_input.setText(f"REG-{row+1:03d}")

    def assign_selected_student(self):
        email = self.email_input.text()
        section = self.class_combo.currentText()
        reg_no = self.reg_no_input.text()

        students = db_manager.load_students()
        if email in students:
            students[email]["section"] = section
            students[email]["reg_no"] = reg_no
            db_manager.save_students(students)
            QMessageBox.information(self, "Success", f"{email} assigned to {section} with Reg No: {reg_no}")
        else:
            QMessageBox.warning(self, "Error", "Student record not found.")

    def create_attendance_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        self.attendance_table = QTableWidget()
        self.attendance_table.setColumnCount(4)
        self.attendance_table.setHorizontalHeaderLabels(["Name", "Reg No", "Period", "Status"])
        self.load_attendance_data()

        layout.addWidget(self.attendance_table)
        tab.setLayout(layout)
        return tab

    def load_attendance_data(self):
        path = "data/attendance_logs.csv"
        if not os.path.exists(path):
            return
        with open(path, newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            self.attendance_table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j in range(len(row)):
                    item = QTableWidgetItem(row[j])
                    if row[3].lower() == "present":
                        item.setIcon(QIcon.fromTheme("dialog-apply"))
                    self.attendance_table.setItem(i, j, item)


class AdminLogin(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.resize(300, 150)

        layout = QVBoxLayout()
        self.label = QLabel("Login Portal")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        
        # Set cursor to pointing hand when hovering over the login button
        self.login_btn.setCursor(Qt.PointingHandCursor)

        layout.addWidget(self.label)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)
        self.setLayout(layout)

    def login(self):
        user = self.username.text()
        pwd = self.password.text()
        if user == "admin" and pwd == "admin":
            self.hide()
            self.dashboard = AdminDashboard(login_screen=self)
            self.dashboard.show()
        elif user == "student" and pwd == "student":
            self.hide()
            self.portal = StudentPortal()
            self.portal.show()
        else:
            self.label.setText("Invalid Credentials")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = AdminLogin()
    login.show()
    sys.exit(app.exec_())
>>>>>>> 027277a (Initial commit)
