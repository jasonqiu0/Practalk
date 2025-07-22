from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QApplication, QHBoxLayout
from PyQt5.QtCore import QTimer, pyqtSignal, QObject, pyqtSlot, QEvent, QCoreApplication
import os
import json
import threading
import time
import sys
from audio import record_audio
from whisper_config import transcribe  
from grader import grade_text
import random

RecordingFinishedEventType = QEvent.Type(QEvent.registerEventType())

class RecordingFinishedEvent(QEvent):
    def __init__(self):
        super().__init__(RecordingFinishedEventType)

class Worker(QObject):

    transcription_finished = pyqtSignal(str, str)
    transcription_error = pyqtSignal(str)

    def __init__(self, audio_file, current_text):
        super().__init__()
        self.audio_file = audio_file
        self.current_text = current_text

    @pyqtSlot()
    def run(self):
        try:
            if self.audio_file and os.path.exists(self.audio_file):
                transcribed_text = transcribe(self.audio_file)
                graded_html, _ = grade_text(self.current_text, transcribed_text)
                self.transcription_finished.emit(transcribed_text, graded_html)
            else:
                self.transcription_error.emit("No audio file to transcribe")
        except Exception as e:
            self.transcription_error.emit(f"Transcription error: {e}")

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
        
        # Remove the status label text
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "font-size: 14px; color: #666; margin-top: 10px; margin-left: 350px; margin-right: 350px;"
        )
        layout.addWidget(self.status_label)


        self.button_layout = QHBoxLayout()

        self.record_button = QPushButton("Start Recording")
        self.record_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;"
        )
        self.record_button.clicked.connect(self.toggle_recording)
        self.button_layout.addWidget(self.record_button)

        self.restart_button = QPushButton("Restart")
        self.restart_button.setStyleSheet(
            "background-color: #c9a84c; color: white; font-size: 16px; padding: 10px;"
        )
        self.restart_button.clicked.connect(self.restart_practice)
        self.restart_button.hide()
        self.button_layout.addWidget(self.restart_button)

        self.next_button = QPushButton("Next")
        self.next_button.setStyleSheet(
            "background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;"
        )
        self.next_button.clicked.connect(self.next_practice)
        self.next_button.hide()
        self.button_layout.addWidget(self.next_button)
        
        layout.addLayout(self.button_layout)
        
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
        self.transcription_thread = None
        self.available_ids = []
        self.current_id = None

        layout.addStretch()

        self.load_text(randomize=True)

    def load_text(self, randomize=False, specific_id=None):
        self.status_label.setText("")
        self.text_display.setText("Loading text...")
        self.transcription_label.setText("Transcription will appear here")
        
        # Show record button, hide others
        self.record_button.show()
        self.record_button.setEnabled(True)
        self.restart_button.hide()
        self.next_button.hide()

        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            json_path = os.path.join(current_dir, 'resources', 'texts.json')
            with open(json_path, 'r') as f:
                texts = json.load(f)
                if not self.available_ids:
                    self.available_ids = [item['id'] for item in texts]
                # Determine which id to use
                if specific_id is not None:
                    chosen_id = specific_id
                elif randomize:
                    chosen_id = random.choice(self.available_ids)
                else:
                    chosen_id = self.current_id if self.current_id is not None else self.available_ids[0]
                self.current_id = chosen_id
                for item in texts:
                    if item['id'] == chosen_id:
                        self.current_text = item['text']
                        self.text_display.setText(item['text'])
                        self.word_count = len(self.current_text.split())
                        self.target_time = min(30, (self.word_count / 140) * 60)
                        break
                else:
                    self.text_display.setText("Text with selected ID not found")
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
            "background-color: #f44336; color: white; font-size: 16px; padding: 10px;"
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
            QCoreApplication.postEvent(self, RecordingFinishedEvent())
        except Exception as e:
            print(f"Recording error: {str(e)}")

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
                "background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;"
            )
            self.status_label.setText("Processing recording...")
            self.record_button.hide()

    def customEvent(self, event):
        if event.type() == RecordingFinishedEventType:
            self.run_transcription()

    def run_transcription(self):
        self.status_label.setText("Transcribing audio...")
        self.record_button.hide()
        
        self.worker = Worker(self.audio_file, self.current_text)
        self.transcription_thread = threading.Thread(target=self.worker.run)
        
        self.worker.transcription_finished.connect(self.on_transcription_finished)
        self.worker.transcription_error.connect(self.on_transcription_error)
        
        self.transcription_thread.start()

    @pyqtSlot(str, str)
    def on_transcription_finished(self, transcribed_text, graded_html):
        self.text_display.setText(graded_html)
        self.transcription_label.setText(f"{transcribed_text}")
        self.status_label.setText("")  # Clear status label
        self.transcription_thread = None

        # Show Restart and Next buttons
        self.record_button.hide()
        self.restart_button.show()
        self.next_button.show()

    @pyqtSlot(str)
    def on_transcription_error(self, error_msg):
        self.transcription_label.setText(error_msg)
        self.status_label.setText("Error. Ready to record again.")
        print(error_msg)
        self.transcription_thread = None
        self.record_button.hide()
        self.restart_button.show()
        self.next_button.hide()

    def restart_practice(self):
        self.load_text(specific_id=self.current_id)

    def next_practice(self):

        if len(self.available_ids) > 1:
            next_ids = [i for i in self.available_ids if i != self.current_id]
            next_id = random.choice(next_ids)
            self.load_text(specific_id=next_id)
        else:
            self.load_text(specific_id=self.current_id)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())