import sounddevice as sd
import soundfile as sf

def record_audio(filename="temp.wav", duration=3, fs=44100, channels=1):
    print(f"Recording for {duration} seconds...")
    
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels)
    sd.wait()  
    
    print("Recording complete. Saving to file...")
    sf.write(filename, recording, fs)
    print(f"Saved: {filename}")

record_audio()
