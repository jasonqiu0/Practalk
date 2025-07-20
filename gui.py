from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Practalk: English Speaking Practice")
        self.setGeometry(100, 100, 800, 600) 
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        title_label = QLabel("Welcome to Practalk!")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)
        
        self.text_display = QLabel("Sample text will appear here...")
        self.text_display.setStyleSheet("font-size: 18px; margin: 20px;")
        layout.addWidget(self.text_display)
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 16px; padding: 10px; margin-left: 350px; margin-right: 350px;"
        )
        layout.addWidget(self.record_button)
        
        layout.addStretch()