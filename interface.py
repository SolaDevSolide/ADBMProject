import os
import sys

import cx_Oracle
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QTabWidget, QLabel, QPushButton,
    QLineEdit, QMessageBox, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QComboBox, QDialog
)
from dotenv import load_dotenv

# Example window function or advanced queries for demonstration
COMPLEX_QUERIES = [
    # 1) Join multiple tables
    ("Join: PlayerStats & Player & Team", """
     SELECT pl.player_name, ps.kills, ps.deaths, ps.assists, t.team_name
     FROM PlayerStats ps
     JOIN Player pl ON ps.player_id = pl.player_id
     JOIN Team t ON ps.team_id = t.team_id
     WHERE ROWNUM <= 20
     """),
    # 2) Analytical function: SUM or AVG
    ("Analytical: AVG kills by champion", """
     SELECT c.champion_name, AVG(ps.kills) AS avg_kills
     FROM PlayerStats ps
     JOIN Champion c ON ps.champion_id = c.champion_id
     GROUP BY c.champion_name
     ORDER BY avg_kills DESC
     """),
    # 3) Nested Query
    ("Nested Query: Players with kills above avg", """
     SELECT p.player_name, ps.kills
     FROM PlayerStats ps
     JOIN Player p ON ps.player_id = p.player_id
     WHERE ps.kills > (
        SELECT AVG(kills) FROM PlayerStats
     )
     AND ROWNUM <= 20
     """),
    # 4) Window Function
    ("Window Function: Running total of kills", """
     SELECT p.player_name,
            ps.kills,
            SUM(ps.kills) OVER (ORDER BY ps.game_id) AS running_kills
     FROM PlayerStats ps
     JOIN Player p ON ps.player_id = p.player_id
     WHERE ROWNUM <= 20
     """),
    # 5) Another join/subquery
    ("Join: TeamStats & Team subquery example", """
     SELECT t.team_name, ts.game_id, ts.total_kills, ts.total_deaths
     FROM TeamStats ts
     JOIN Team t ON ts.team_id = t.team_id
     WHERE ts.total_kills > (
       SELECT AVG(total_kills) FROM TeamStats
     )
     AND ROWNUM <= 20
     """),
    # 6) Another aggregated query
    ("Aggregated Kills by Patch", """
     SELECT g.patch, SUM(ps.kills) AS total_kills
     FROM PlayerStats ps
     JOIN Game g ON ps.game_id = g.game_id
     GROUP BY g.patch
     ORDER BY total_kills DESC
     """)
]

class LoginDialog(QDialog):
    """
    Simple login dialog to capture user credentials and role selection,
    returning them to the main window for Oracle connection.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LoL Worlds DB Login")
        self.setFixedSize(300, 180)

        layout = QVBoxLayout()

        self.user_label = QLabel("Username:")
        self.user_input = QLineEdit()
        layout.addWidget(self.user_label)
        layout.addWidget(self.user_input)

        self.pass_label = QLabel("Password:")
        self.pass_input = QLineEdit()
        self.pass_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pass_label)
        layout.addWidget(self.pass_input)

        self.role_label = QLabel("Role:")
        self.role_box = QComboBox()
        self.role_box.addItems(["admin_user", "manager_user", "regular_user"])
        layout.addWidget(self.role_label)
        layout.addWidget(self.role_box)

        btn_layout = QHBoxLayout()
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.attempt_login)
        btn_layout.addWidget(self.login_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self._username = None
        self._password = None
        self._role = None

    def attempt_login(self):
        """
        Collects login info and closes dialog if successful.
        """
        user = self.user_input.text().strip()
        passwd = self.pass_input.text().strip()
        role = self.role_box.currentText()
        if not user or not passwd:
            QMessageBox.warning(self, "Login Failed", "Username/Password cannot be empty")
            return
        self._username = user
        self._password = passwd
        self._role = role
        self.accept()

    def get_credentials(self):
        return self._username, self._password, self._role


class MainWindow(QMainWindow):
    """
    Main application window with multiple tabs:
      1) Queries Tab (run the 6 complex queries, show results).
      2) Graph Tab (display a matplotlib chart).
      3) Modify DB Tab (insert, update, delete if privileges allow).
    """
    def __init__(self, host, port, service, username, password, role):
        super().__init__()
        self.setWindowTitle("LoL Worlds Modern Interface")
        self.setGeometry(100, 100, 1000, 600)

        self.host = host
        self.port = port
        self.service = service
        self.db_username = username
        self.db_password = password
        self.role = role

        self.connection = None
        self.init_db_connection()

        tab_widget = QTabWidget()
        tab_widget.addTab(self.create_queries_tab(), "Queries")
        tab_widget.addTab(self.create_graph_tab(), "Graphs")
        tab_widget.addTab(self.create_modify_tab(), "Modify DB")

        self.setCentralWidget(tab_widget)

    def init_db_connection(self):
        """
        Initiates cx_Oracle connection with user credentials.
        """
        dsn_str = f"{self.host}:{self.port}/{self.service}"
        try:
            self.connection = cx_Oracle.connect(
                user=self.db_username,
                password=self.db_password,
                dsn=dsn_str
            )
            print("Connected as role:", self.role)
        except cx_Oracle.Error as e:
            QMessageBox.critical(self, "DB Error", f"Failed to connect: {e}")
            sys.exit(1)

    def create_queries_tab(self):
        """
        Creates a tab containing 6 queries from COMPLEX_QUERIES, each with a button to run
        and a table to display results.
        """
        container = QWidget()
        layout = QVBoxLayout(container)

        # We'll hold a reference to a QTableWidget to display results
        self.query_table = QTableWidget()
        layout.addWidget(self.query_table)

        # Buttons for each query
        for title, sql in COMPLEX_QUERIES:
            btn = QPushButton(title)
            btn.clicked.connect(lambda checked, s=sql: self.run_query(s))
            layout.addWidget(btn)

        return container

    def run_query(self, sql):
        """
        Runs the chosen complex query, populates the QTableWidget with results.
        """
        if not self.connection:
            QMessageBox.warning(self, "Warning", "No DB Connection")
            return
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description]
            self.query_table.setColumnCount(len(col_names))
            self.query_table.setRowCount(len(rows))
            self.query_table.setHorizontalHeaderLabels(col_names)

            for r_index, row_data in enumerate(rows):
                for c_index, val in enumerate(row_data):
                    self.query_table.setItem(r_index, c_index, QTableWidgetItem(str(val)))
            self.query_table.resizeColumnsToContents()
            cursor.close()
        except cx_Oracle.Error as e:
            QMessageBox.critical(self, "Query Error", f"Error running query: {e}")

    def create_graph_tab(self):
        """
        Creates a tab that can display a matplotlib chart based on a query.
        We'll demonstrate one example: champion name vs average kills.
        """
        container = QWidget()
        layout = QVBoxLayout(container)

        # Button that will run a query and display a bar chart
        chart_btn = QPushButton("Show Champion vs AVG Kills Chart")
        chart_btn.clicked.connect(self.show_champion_avg_kills_chart)
        layout.addWidget(chart_btn)

        self.chart_label = QLabel("Graph will appear in a separate Matplotlib window.")
        layout.addWidget(self.chart_label)

        return container

    def show_champion_avg_kills_chart(self):
        """
        Runs a query to get champion name + avg kills, then displays a bar chart in a new figure.
        """
        sql = """
        SELECT c.champion_name, AVG(ps.kills) as avg_kills
        FROM PlayerStats ps
        JOIN Champion c ON ps.champion_id = c.champion_id
        GROUP BY c.champion_name
        ORDER BY avg_kills DESC
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute(sql)
            data = cursor.fetchall()
            cursor.close()

            champs = [row[0] for row in data]
            avgs  = [float(row[1]) for row in data]

            # Limit the chart to the top 10 champions for readability
            champs = champs[:10]
            avgs = avgs[:10]

            plt.figure(figsize=(8,5))
            plt.bar(champs, avgs, color='skyblue')
            plt.title("Top 10 Champions by Avg Kills")
            plt.ylabel("Avg Kills")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.show()
        except cx_Oracle.Error as e:
            QMessageBox.critical(self, "Chart Error", f"Error running chart query: {e}")

    def create_modify_tab(self):
        """
        Creates a tab that allows the user to run insert, update, or delete statements if they have privileges.
        If the role is 'regular_user', we'll disable the input fields.
        """
        container = QWidget()
        layout = QVBoxLayout(container)

        # We can provide a text box for a custom DML statement (INSERT, UPDATE, DELETE)
        self.dml_input = QLineEdit()
        self.dml_input.setPlaceholderText("Write INSERT / UPDATE / DELETE statement here...")
        layout.addWidget(self.dml_input)

        run_btn = QPushButton("Run DML Statement")
        run_btn.clicked.connect(self.run_dml)
        layout.addWidget(run_btn)

        # If user is 'regular_user', disable these inputs
        if self.role == "regular_user":
            self.dml_input.setDisabled(True)
            run_btn.setDisabled(True)
            info_label = QLabel("You do not have privileges to modify data.")
            layout.addWidget(info_label)

        return container

    def run_dml(self):
        """
        Attempts to run the user-provided INSERT / UPDATE / DELETE statement if the user has privileges.
        """
        dml_statement = self.dml_input.text()
        if not dml_statement.strip():
            QMessageBox.warning(self, "Warning", "No DML statement entered.")
            return

        try:
            cursor = self.connection.cursor()
            cursor.execute(dml_statement)
            self.connection.commit()
            cursor.close()
            QMessageBox.information(self, "Success", "DML executed successfully.")
        except cx_Oracle.Error as e:
            QMessageBox.critical(self, "DML Error", f"Error running DML: {e}")


def main():
    # Load environment variables from .env file
    load_dotenv("/")

    # Get DB connection details from .env
    ORA_HOST = os.getenv("ORA_HOST", "localhost")
    ORA_PORT = os.getenv("ORA_PORT", "1521")
    ORA_SERVICE = os.getenv("ORA_SERVICE", "PDB1")
    SYS_PASS = os.getenv("SYS_PASS")
    ADMIN_USER_PASS = os.getenv("ADMIN_USER_PASS")
    MANAGER_USER_PASS = os.getenv("MANAGER_USER_PASS")
    REGULAR_USER_PASS = os.getenv("REGULAR_USER_PASS")

    app = QApplication(sys.argv)

    # Prompt the user for credentials and role selection
    login_dialog = LoginDialog()
    if login_dialog.exec_() == login_dialog.Accepted:
        username, password, role = login_dialog.get_credentials()
    else:
        sys.exit(0)

    window = MainWindow(host, port, service, username, password, role)
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()