import sounddevice as sd
import soundfile as sf

def record_audio(duration, sample_rate=16000):
    print(f"Recording for {duration} seconds...")
    recording = sd.rec(int(duration * sample_rate), 
                      samplerate=sample_rate, 
                      channels=1,
                      blocking=True)
    sf.write('temp.wav', recording, sample_rate)
    return 'temp.wav'