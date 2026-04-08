import sys
import socket
from PyQt6.QtWidgets import QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout, QWidget, QLabel
from PyQt6.QtCore import QProcess
from PyQt6.QtGui import QFont, QTextCursor

class ServerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Reliable UDP Server - Control Panel")
        self.resize(700, 500)

        # --------------------------------------------------------
        # UI Setup
        # --------------------------------------------------------
        layout = QVBoxLayout()

        # NEW: Fetch and display the local network IP
        local_ip = self.get_local_ip()
        self.ip_label = QLabel(f"🌐 Server Network IP: {local_ip}")
        self.ip_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.ip_label.setStyleSheet("""
            QLabel {
                color: #58a6ff; 
                padding: 5px;
                background-color: #1e1e1e;
                border-radius: 5px;
                border: 1px solid #333333;
            }
        """)

        # The terminal output window
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Consolas", 10))
        self.console_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 2px solid #333333;
                border-radius: 5px;
                padding: 5px;
            }
        """)

        # The Start/Stop Button
        self.btn_toggle = QPushButton("Start Server")
        self.btn_toggle.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.btn_toggle.setStyleSheet("""
            QPushButton {
                background-color: #2ea043;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3fb950;
            }
        """)
        self.btn_toggle.clicked.connect(self.toggle_server)

        # Add widgets to layout
        layout.addWidget(self.ip_label)      # Added the IP label to the top
        layout.addWidget(self.console_output)
        layout.addWidget(self.btn_toggle)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # --------------------------------------------------------
        # Process Setup (This runs your server.py)
        # --------------------------------------------------------
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)
        self.process.stateChanged.connect(self.handle_state)

    def get_local_ip(self):
        """Trick to get the actual LAN IP address instead of just 127.0.0.1"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Doesn't have to be reachable, just forces the OS to route a packet 
            # so we can see which local IP it uses.
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def toggle_server(self):
        # If server is not running, start it
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self.console_output.clear()
            self.console_output.append(">>> Starting server.py...")
            
            # The '-u' flag is CRITICAL. It forces Python to print to the GUI instantly 
            # instead of buffering the output invisibly.
            self.process.start("python", ["-u", "server.py"])
            
            self.btn_toggle.setText("Stop Server")
            self.btn_toggle.setStyleSheet("""
                QPushButton { background-color: #da3633; color: white; padding: 10px; border-radius: 5px;}
                QPushButton:hover { background-color: #f85149; }
            """)
        else:
            # If server is running, kill it
            self.console_output.append("\n>>> Stopping server.py...")
            self.process.kill()

    def handle_stdout(self):
        # Grab normal print() outputs from server.py and put them in the text box
        data = self.process.readAllStandardOutput().data().decode('utf-8')
        self.console_output.insertPlainText(data)
        self.console_output.moveCursor(QTextCursor.MoveOperation.End)

    def handle_stderr(self):
        # Grab error messages from server.py (so you don't miss crashes)
        data = self.process.readAllStandardError().data().decode('utf-8')
        self.console_output.insertPlainText(f"[ERROR] {data}")
        self.console_output.moveCursor(QTextCursor.MoveOperation.End)

    def handle_state(self, state):
        # Reset the button if the server crashes or stops
        if state == QProcess.ProcessState.NotRunning:
            self.btn_toggle.setText("Start Server")
            self.btn_toggle.setStyleSheet("""
                QPushButton { background-color: #2ea043; color: white; padding: 10px; border-radius: 5px;}
                QPushButton:hover { background-color: #3fb950; }
            """)

    def closeEvent(self, event):
        # Make sure the background python script dies when you close the GUI window
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()
            self.process.waitForFinished(1000)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ServerGUI()
    window.show()
    sys.exit(app.exec())