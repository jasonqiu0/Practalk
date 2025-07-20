import sounddevice as sd
import soundfile as sf
import numpy as np
import queue
import time  # Add this import

def record_audio(filename="temp.wav", duration=30, fs=44100, channels=1, stop_event=None):
    print(f"Recording to {filename}... (max {duration} seconds)")
    
    audio_queue = queue.Queue()
    
    def callback(indata, frames, time_info, status):
        if status:
            print(status)
        audio_queue.put(indata.copy())
    
    stream = sd.InputStream(
        samplerate=fs,
        channels=channels,
        callback=callback
    )
    stream.start()
    
    recording = []
    start_time = time.time()  
    
    while True:
        if stop_event and stop_event.is_set():
            break
        if time.time() - start_time >= duration:  
            break
        
        try:
            data = audio_queue.get(timeout=0.1)
            recording.append(data)
        except queue.Empty:
            continue
    
    stream.stop()
    stream.close()
    
    if recording:
        recording = np.concatenate(recording, axis=0)
        
        sf.write(filename, recording, fs)
        print(f"Recording saved to {filename}")
        actual_duration = time.time() - start_time  
        return filename, actual_duration
    else:
        print("No audio recorded")
        return None, 0