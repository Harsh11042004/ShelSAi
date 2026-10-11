import sounddevice as sd
import numpy as np

print("Recording for 5 seconds. Speak normally!")

audio = sd.rec(
    int(5 * 16000),
    samplerate=16000,
    channels=1,
    dtype="int16"
)

sd.wait()

audio = audio.astype(np.float32)

rms = np.sqrt(np.mean(audio ** 2))
peak = np.max(np.abs(audio))

print(f"Average audio level: {rms:.2f}")
print(f"Peak audio level: {peak:.2f}")

if rms < 100:
    print("Warning: Audio level is very low. Check your microphone.")
elif rms > 15000:
    print("Warning: Audio level is quite high. Check for clipping.")
else:
    print("Audio captured. Levels look plausible.")