<<<<<<< HEAD
# main.py

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout
from admin_portal import AdminDashboard
from student_portal import StudentPortal

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login Portal")
        self.resize(300, 150)

        layout = QVBoxLayout()
        self.label = QLabel("Login as Admin or Student")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)

        layout.addWidget(self.label)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def login(self):
        user = self.username.text().lower()
        pwd = self.password.text()

        if user == "admin" and pwd == "admin":
            self.close()
            self.dashboard = AdminDashboard()
            self.dashboard.show()
        elif user == "student" and pwd == "student":
            self.close()
            self.portal = StudentPortal()
            self.portal.show()
        else:
            self.label.setText("Invalid Credentials. Try again.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
=======
# main.py

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout
from admin_portal import AdminDashboard
from student_portal import StudentPortal

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login Portal")
        self.resize(300, 150)

        layout = QVBoxLayout()
        self.label = QLabel("Login as Admin or Student")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)

        layout.addWidget(self.label)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def login(self):
        user = self.username.text().lower()
        pwd = self.password.text()

        if user == "admin" and pwd == "admin":
            self.close()
            self.dashboard = AdminDashboard()
            self.dashboard.show()
        elif user == "student" and pwd == "student":
            self.close()
            self.portal = StudentPortal()
            self.portal.show()
        else:
            self.label.setText("Invalid Credentials. Try again.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
>>>>>>> 027277a (Initial commit)
