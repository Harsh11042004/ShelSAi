import queue
import threading
from collections import deque

import numpy as np
import sounddevice as sd
import speech_recognition as sr


SAMPLE_RATE = 16000
BLOCK_SIZE = 4000
CALIBRATION_BLOCKS = 4
MIN_SPEECH_THRESHOLD = 180
SPEECH_THRESHOLD_MULTIPLIER = 2.5
SILENCE_BLOCKS = 3
MAX_UTTERANCE_BLOCKS = 120
GOOGLE_REQUEST_TIMEOUT = 15


def _transcribe_worker(recognizer, language, utterance_queue, result_queue):
    while True:
        audio = utterance_queue.get()
        if audio is None:
            return

        audio_data = sr.AudioData(audio.tobytes(), SAMPLE_RATE, 2)
        try:
            text = recognizer.recognize_google(audio_data, language=language)
        except sr.UnknownValueError:
            print("Speech was captured, but Google could not recognize the words.")
        except sr.RequestError as error:
            print(f"Google speech recognition request failed: {error}")
        else:
            if text.strip():
                result_queue.put(text.strip())


def start_listening(language="en-US", on_transcription=None):
    recognizer = sr.Recognizer()
    recognizer.operation_timeout = GOOGLE_REQUEST_TIMEOUT
    audio_queue = queue.Queue(maxsize=64)
    utterance_queue = queue.Queue(maxsize=10)
    status_queue = queue.Queue()
    audio_dropped = threading.Event()
    result_queue = queue.Queue()

    transcription_thread = threading.Thread(
        target=_transcribe_worker,
        args=(recognizer, language, utterance_queue, result_queue),
        daemon=True,
    )
    transcription_thread.start()

    print("Listening with Google speech recognition.")
    print("Audio is sent to Google for transcription. Press Ctrl+C to stop.")
    print("Keep quiet for one second while the microphone calibrates.")
    print("Activation word: 'Kestrel' (Google may transcribe it as 'Castrol').")
    print("Say it before each command.")

    def callback(indata, frames, time, status):
        if status:
            status_queue.put(str(status))
        try:
            audio_queue.put_nowait(bytes(indata))
        except queue.Full:
            audio_dropped.set()

    pre_roll = deque(maxlen=2)
    utterance = []
    silence_count = 0
    speech_active = False
    ambient_levels = []
    speech_threshold = MIN_SPEECH_THRESHOLD

    def submit_utterance():
        nonlocal utterance, silence_count, speech_active
        if utterance:
            audio = np.concatenate(utterance)
            try:
                utterance_queue.put_nowait(audio)
            except queue.Full:
                print("Transcription queue is full; this phrase was skipped.")
        utterance = []
        silence_count = 0
        speech_active = False

    try:
        with sd.RawInputStream(
            samplerate=SAMPLE_RATE,
            blocksize=BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            while True:
                while True:
                    try:
                        transcript = result_queue.get_nowait()
                    except queue.Empty:
                        break
                    print(f"Recognized: {transcript}")
                    if on_transcription is not None and on_transcription(transcript) is False:
                        print("Stopping speech recognition...")
                        return

                if audio_dropped.is_set():
                    audio_dropped.clear()
                    print("Audio warning: capture is falling behind; some audio was skipped.")

                while True:
                    try:
                        print(f"Audio input warning: {status_queue.get_nowait()}")
                    except queue.Empty:
                        break

                try:
                    audio_bytes = audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                samples = np.frombuffer(audio_bytes, dtype=np.int16)
                level = np.sqrt(np.mean(samples.astype(np.float32) ** 2))

                if len(ambient_levels) < CALIBRATION_BLOCKS:
                    ambient_levels.append(level)
                    if len(ambient_levels) == CALIBRATION_BLOCKS:
                        ambient_level = float(np.median(ambient_levels))
                        speech_threshold = max(
                            MIN_SPEECH_THRESHOLD,
                            ambient_level * SPEECH_THRESHOLD_MULTIPLIER,
                        )
                        print("Microphone calibrated. Speak naturally.")
                    continue

                is_speech = level >= speech_threshold
                if not speech_active:
                    pre_roll.append(samples.copy())
                    if is_speech:
                        speech_active = True
                        utterance.extend(pre_roll)
                        pre_roll.clear()
                        silence_count = 0
                    continue

                utterance.append(samples.copy())
                if is_speech:
                    silence_count = 0
                else:
                    silence_count += 1

                if silence_count >= SILENCE_BLOCKS or len(utterance) >= MAX_UTTERANCE_BLOCKS:
                    submit_utterance()
                    pre_roll.clear()

    except KeyboardInterrupt:
        if utterance:
            submit_utterance()
        print("\nStopping speech recognition...")
    finally:
        utterance_queue.put(None)
        transcription_thread.join()
        print("ShelSAi speech recognition stopped.")
