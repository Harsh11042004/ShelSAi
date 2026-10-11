from enum import Enum


WAKE_WORDS = {"kestrel", "castrol", "castor"}


class State(Enum):
    launch = "Command"
    exit = "Exit"
    default = "Idle"


def command_state(text):
    words = [word.strip(".,!?;:") for word in text.casefold().split()]
    if not words or words[0] not in WAKE_WORDS:
        return State.default

    words = words[1:]
    if words and words[0] == "exit":
        return State.exit
    if "open" in words or "launch" in words:
        return State.launch
    return State.default
