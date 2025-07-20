from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QApplication
from PyQt5.QtCore import QTimer
import os
import json
import threading
import time
import sys
from audio import record_audio
from whisper_config import transcribe  

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
        self.text_display.setStyleSheet(
            "font-size: 20px; margin: 20px; border: 2px solid #ccc; "
            "padding: 15px; border-radius: 5px; word-spacing: 3px; letter-spacing: 1.2px;"
        )
        self.text_display.setWordWrap(True)
        layout.addWidget(self.text_display)
        
        self.status_label = QLabel("Ready to record")
        self.status_label.setStyleSheet(
            "font-size: 14px; color: #666; margin-top: 10px; margin-left: 350px; margin-right: 350px;"
        )
        layout.addWidget(self.status_label)

        self.record_button = QPushButton("Start Recording")
        self.record_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 16px; "
            "padding: 10px; margin-left: 350px; margin-right: 350px;"
        )
        self.record_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.record_button)
        
        self.transcription_label = QLabel("Transcription will appear here")
        self.transcription_label.setStyleSheet(
            "font-size: 18px; margin: 20px; border: 2px solid #eee;"
            "padding: 15px; border-radius: 5px; background-color: #333333;"
        )
        self.transcription_label.setWordWrap(True)
        layout.addWidget(self.transcription_label)
        
        self.recording = False
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.update_recording_timer)
        self.seconds_recorded = 0
        self.stop_event = None
        self.recording_thread = None
        self.audio_file = None
        self.actual_duration = 0

        layout.addStretch()

        self.load_text()

    def load_text(self):
        """Load practice text from JSON file"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, 'resources', 'texts.json')

            with open(json_path, 'r') as f:
                texts = json.load(f)
                for item in texts:
                    if item['id'] == 1:
                        self.current_text = item['text']
                        self.text_display.setText(item['text'])
                        
                        self.word_count = len(self.current_text.split())
                        self.target_time = min(30, (self.word_count / 140) * 60)
                        self.status_label.setText(f"Target time: {self.target_time:.1f} seconds")
                        break
                else:
                    self.text_display.setText("Text with ID 1 not found")
        except FileNotFoundError:
            self.text_display.setText("Texts file not found")
        except json.JSONDecodeError:
            self.text_display.setText("Error reading texts file")

    def toggle_recording(self):
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        if self.stop_event:
            self.stop_event.clear()
        else:
            self.stop_event = threading.Event()
        
        self.recording = True
        self.record_button.setText("Stop Recording")
        self.record_button.setStyleSheet(
            "background-color: #f44336; color: white; font-size: 16px; "
            "padding: 10px; margin-left: 350px; margin-right: 350px;"
        )
        self.status_label.setText("Recording... 0s")
        self.seconds_recorded = 0
        self.transcription_label.setText("") 
        
        self.record_timer.start(1000) 
        
        self.recording_thread = threading.Thread(
            target=self.run_recording, args=(self.stop_event,)
        )
        self.recording_thread.start()

    def run_recording(self, stop_event):
        try:
            self.audio_file, self.actual_duration = record_audio(
                duration=30, 
                stop_event=stop_event
            )
            
            QApplication.instance().postEvent(self, RecordingFinishedEvent())
        except Exception as e:
            print(f"Recording error: {str(e)}")
            self.status_label.setText(f"Recording error: {str(e)}")

    def update_recording_timer(self):
        if self.recording:
            self.seconds_recorded += 1
            self.status_label.setText(f"Recording... {self.seconds_recorded}s")
            
            
            if self.seconds_recorded >= 30:
                self.stop_recording()

    def stop_recording(self):
        if self.recording:
           
            if self.stop_event:
                self.stop_event.set()

            self.recording = False
            self.record_timer.stop()
            self.record_button.setText("Start Recording")
            self.record_button.setStyleSheet(
                "background-color: #4CAF50; color: white; font-size: 16px; "
                "padding: 10px; margin-left: 350px; margin-right: 350px;"
            )
            self.status_label.setText("Processing recording...")
            
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=1.0)
            
          
            self.display_results()
            
            threading.Thread(target=self.run_transcription).start()

    def display_results(self):
        if self.actual_duration > 0:
            wpm = (self.word_count / self.actual_duration) * 60
            
            # Generate feedback
            if wpm < 120:
                feedback = "Too slow for conversation (aim for 140 WPM)"
            elif wpm > 160:
                feedback = "Too fast, focus on clarity"
            elif wpm < 130:
                feedback = "Slightly slow, try to speed up a bit"
            elif wpm > 150:
                feedback = "Slightly fast, try to slow down a bit"
            else:
                feedback = "Perfect conversational pace!"
            
            self.status_label.setText(
                f"Recorded: {self.actual_duration:.1f}s | "
                f"WPM: {wpm:.1f} | {feedback}"
            )
        else:
            self.status_label.setText("Recording failed or was too short")

    def run_transcription(self):
        try:
            if self.audio_file and os.path.exists(self.audio_file):

                self.transcription_label.setText("Transcribing audio...")
                
                transcribed_text = transcribe(self.audio_file)
                
                self.transcription_label.setText(
                    f"{transcribed_text}"
                )
            else:
                self.transcription_label.setText("No audio file to transcribe")
        except Exception as e:
            print(f"Transcription error: {str(e)}")
            self.transcription_label.setText(f"Transcription error: {str(e)}")

class RecordingFinishedEvent:
    pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())