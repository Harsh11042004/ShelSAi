print("================================")
print("       Welcome to ShelSAi       ")
print("================================")

print("ShelSAi is ready for development.\n")

from speech_to_text import start_listening
from state import command_state, State
from command import execute_command


def handle_transcription(text):
    state = command_state(text)

    if state == State.exit:
        print("Kestrel exit recognized. ShelSAi is shutting down.")
        return False
    if state == State.launch:
        print("Wake phrase recognized. Executing command.")
        execute_command(text)
    elif state == State.default:
        print("Wake phrase not detected; staying idle.")
    return True


start_listening(on_transcription=handle_transcription)
