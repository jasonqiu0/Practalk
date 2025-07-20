from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
import os
import json
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Practalk: English Speaking Practice")
        self.setGeometry(100, 100, 800, 600) 
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        title_label = QLabel("Practalk")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-top: 20px;")
        layout.addWidget(title_label)
        
        self.text_display = QLabel("Loading text...")
        self.text_display.setStyleSheet("font-size: 20px; margin: 20px; border: 2px solid #ccc; padding: 15px; border-radius: 5px; word-spacing: 3px; letter-spacing: 1.2px")
        self.text_display.setWordWrap(True)
        layout.addWidget(self.text_display)
        
        self.record_button = QPushButton("Start Recording")
        self.record_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 16px; padding: 10px; margin-left: 350px; margin-right: 350px;"
        )
        layout.addWidget(self.record_button)
        
        layout.addStretch()

        self.load_text()

    def load_text(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, 'resources', 'texts.json')

            with open(json_path, 'r') as f:
                texts = json.load(f)
                for item in texts:
                    if item['id']==1:
                        self.text_display.setText(item['text'])
                        break
                    else:
                        self.text_display.setText("Text with ID 1 not found")
        except FileNotFoundError:
            self.text_display.setText("Texts file not found")
        except json.JSONDecodeError:
            self.text_display.setText("Error reading texts file")