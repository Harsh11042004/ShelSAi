# ShelSAi (Shell Script AI)

ShelSAi is an experimental Windows voice-control application. It continuously
captures speech, sends completed phrases to Google's public speech-recognition
endpoint, and launches an application when a recognized command starts with its
activation word.

> **Project status:** v1 is an early, Windows-only prototype. Expect recognition
> errors and verify each command's transcript before relying on it. It is not
> intended for safety-critical or unattended use.

This guide describes what the code does today, how its pieces fit together,
how to run and troubleshoot it, and where to start when extending it. It does
not treat planned features in the project brief as already implemented.

## Current capabilities and limits

Implemented:

- Continuous microphone capture until the user says an exit command or presses
  Ctrl+C.
- Phrase segmentation based on microphone audio level and silence.
- Online transcription through the `SpeechRecognition` package's
  `recognize_google` method.
- A wake-word gate before application-launch commands are acted on.
- Application lookup using `where.exe` (which searches Windows `PATH`) and
  Windows App Paths registry entries.
- A small set of application-name aliases and direct process launch.
- A separate utility to export installed application display names.

Not currently implemented:

- Google Cloud Speech-to-Text credentials, guaranteed accuracy, or guaranteed
  response time. The public Google endpoint is not a production API.
- A local wake-word detector. The recognizer transcribes every captured phrase,
  and Python checks the transcript afterward.
- Recursive disk-wide executable search. `where.exe` searches `PATH`; the
  registry lookup checks only App Paths entries.
- Dictation, punctuation insertion, backspace correction, shell-command
  execution, mouse/keyboard injection, a screen grid, or a command confirmation
  system.
- A service that starts automatically with Windows.

The project brief describes some of these future capabilities. Use the code,
not the brief, as the source of truth for current behavior.

## Requirements and setup

- Windows, with a working microphone and speakers/headphones.
- Python installed and available on `PATH`.
- An internet connection for Google transcription.
- Python 3.10 or newer.

From PowerShell in the project folder, create and activate a virtual environment,
install dependencies, and start ShelSAi:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

If a virtual environment already exists, install or update the dependencies
with:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

If PowerShell blocks environment activation, use the explicit `.venv\Scripts\python.exe`
commands above instead.

To start after setup, double-click `start_shelsai.bat` or run
`.\.venv\Scripts\python.exe main.py` from the project directory. The batch file
uses its own location, so it does not depend on where the project is installed.

The first second is used to estimate the room's background audio level. Keep
quiet while the program displays `Microphone calibrated. Speak naturally.`

## Using voice commands

The configured activation word is **Kestrel**. Google has transcribed it as
**Castrol** and **Castor** in observed runs, so all three are currently accepted
when they are the first word in the transcript. These alternatives are ordinary
transcript aliases, not separate acoustic wake-word models.

Examples:

```text
Kestrel, open Chrome
Kestrel, launch Visual Studio Code
Castrol, open Zoom
Kestrel, exit
```

The recognizer can produce slightly different wording. ShelSAi prints every
recognized phrase so you can see what it is evaluating. The activation word
must be the first recognized word. Commands without an accepted activation
word are ignored.

`Kestrel exit`, `Castrol exit`, or `Castor exit` shuts down ShelSAi. Ctrl+C in
the console is the manual stop option.

The current command parser recognizes `open` or `launch` after the activation
word as an application-launch request. No dictation command is currently
implemented.

## How the application works

```text
Microphone
  -> sounddevice callback
  -> bounded audio queue
  -> level/silence phrase segmentation
  -> transcription queue
  -> background Google transcription worker
  -> recognized transcript queue
  -> main-thread callback
  -> wake-word/state gate
  -> app lookup and process launch OR exit
```

Audio is mono, 16 kHz, signed 16-bit PCM. Each input block is 4,000 samples
(about 250 ms). Four initial blocks estimate ambient noise. Speech is considered
active above the greater of an RMS level of 180 or 2.5 times that estimate.
Two blocks of pre-roll are retained so the start of a phrase is less likely to
be clipped. A phrase is submitted after three low-level blocks (about 750 ms)
or after a 30-second maximum phrase length.

The input callback only copies audio into a queue; phrase splitting and Google
requests happen outside that callback. A background thread calls
`recognize_google`, with a 15-second operation timeout. Recognized results are
handled by the main listening loop. A slow command lookup can temporarily delay
that loop from draining new audio, so keep voice commands short.

Google transcription is online and audio is sent to Google for processing.
There is no guarantee that speech will be recognized correctly or quickly.
Room noise, microphone gain, accent, network quality, phrase boundaries, and
Google's service all affect the result. Avoid treating recognition as a
security boundary for sensitive operations.

## Privacy and safety

ShelSAi sends microphone audio to Google's public speech-recognition endpoint
for transcription. Do not use it in conversations or environments where
recording or third-party processing is not permitted. Review Google's current
service terms and privacy information before use; this project does not control
that service.

Recognized speech can be wrong. The current implementation launches
applications without a confirmation step, so test with non-critical commands
and keep the microphone muted or the app stopped when it is not in use. Only
application launching is implemented; do not add arbitrary shell execution
without careful validation and a separate security review.

## Installing from a GitHub download

Download and extract the v1 source ZIP, then open a terminal in the extracted
project folder and run the setup commands above. GitHub's source ZIP does not
include the Python virtual environment or downloaded local Vosk model files;
neither is required for the current Google-based speech code. Install the
listed dependencies into a fresh environment on each computer.

Do not publish your `.venv`, machine-specific shortcuts, microphone recordings,
credentials, or private/internal BRD documents. The repository `.gitignore`
excludes common local and generated files, but always review the staged files
before pushing.

## Application lookup and launch

`command.py` normalizes the transcript by removing a supported activation word
and a leading action word such as `open` or `launch`. It then applies aliases
for names such as Google Chrome, Edge, Visual Studio Code, MySQL Workbench,
MongoDB Compass, VirtualBox, Epic Games Launcher, and Zoom.

For lookup, ShelSAi:

1. Runs `where.exe <name>.exe` and prints any paths returned. This finds
   executables available on `PATH`; it does not search every disk or folder.
2. If needed, scans Windows App Paths registry entries under the current-user
   and local-machine hives (including the 32-bit machine view).
3. Uses `shutil.which` as a final `PATH` lookup fallback.
4. Starts the resolved executable with `subprocess.Popen`.

If an installed application is not found, add its executable directory to
`PATH`, register an App Paths entry, or add an explicit alias/path in
`command.py`. Do not execute the recognized speech as an arbitrary shell
command; app launches should remain an allowlisted, validated operation.

## Project files

| File | Responsibility |
| --- | --- |
| `main.py` | Prints the welcome message, receives each transcript, checks command state, and dispatches launch or exit actions. |
| `speech_to_text.py` | Captures microphone input, segments phrases, requests Google transcription, and invokes a callback with results. |
| `state.py` | Defines accepted activation-word spellings and classifies wake-word-prefixed transcripts. |
| `command.py` | Removes command prefixes, applies app aliases, locates executables, and launches them. |
| `get_apps.py` | Reads installed-app display names from uninstall registry keys and writes `my_installed_apps.txt`. |
| `test_microphone.py` | Records five seconds and reports approximate audio RMS and peak levels. |
| `requirements.txt` | Lists Python packages required by the current application. |
| `my_installed_apps.txt` | Generated output from `get_apps.py`; not used by the current launcher. |
| `vosk-model-en-us-0.22-lgraph/` | Old Vosk model assets; safe to delete because the current speech code does not use them. |

Run the optional microphone-level check from the project folder with:

```powershell
.\.venv\Scripts\python.exe test_microphone.py
```

To export the installed application list:

```powershell
.\.venv\Scripts\python.exe get_apps.py
```

The list is written relative to the current working directory.

## Tests

Run the command-state tests from the project folder:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

GitHub Actions runs these tests on Windows with Python 3.10 through 3.13 for
each push and pull request.

## Troubleshooting

### No speech or incorrect transcripts

- Check Windows microphone permissions and select the intended default input
  device.
- Run `test_microphone.py` and confirm its reported audio level is plausible.
- Stay quiet during the initial one-second calibration; speak close enough to
  the mic and avoid clipping.
- Check that the internet connection permits Google speech-recognition
  requests. Request errors are printed by the app.
- Read the `Recognized:` output. If the activation word is consistently
  misheard, update `WAKE_WORDS` in `state.py` and the matching prefix removal
  set in `command.py` to keep them aligned.
- Raise or lower `MIN_SPEECH_THRESHOLD` or
  `SPEECH_THRESHOLD_MULTIPLIER` in `speech_to_text.py` only after checking
  microphone levels. A high threshold can miss quiet speech; a low threshold
  can include noise.

### The app hears the command but doesn't launch anything

- Make sure the recognized transcript begins with an accepted activation word.
- Confirm the action includes `open` or `launch`.
- Check that the app name maps to the expected executable alias.
- Remember that `where.exe` only finds files on `PATH`; an application outside
  `PATH` needs an App Paths entry or an explicit lookup rule.
- Read the printed CMD search results and registry result (if any) to identify
  what lookup found.

### Google request or network failures

Keep the internet connection available. The current integration has no offline
fallback, automatic retry policy, or Google Cloud credential configuration.

### Audio queue warnings

Warnings about capture falling behind mean the audio consumer is not keeping up
with captured blocks. Close CPU-heavy applications, shorten speech commands, or
move slow work out of the listening loop before increasing queue sizes.

## Extending ShelSAi

Useful next steps, from smaller to larger changes:

1. **Add tests for command parsing.** Cover transcripts with punctuation,
   wake-word alternatives, missing wake words, app names with multiple words,
   and exit commands. Keep parsing separate from process launch so tests do not
   open real applications.
2. **Make app resolution explicit.** Store aliases and approved executable
   paths in a structured configuration, show the selected match, and ask for
   confirmation when a name is ambiguous.
3. **Improve recognition reliability.** Tune phrase detection with recorded
   test samples. For supported production use, evaluate Google Cloud
   Speech-to-Text or another documented API, including its credentials, costs,
   privacy, latency, and retry behavior.
4. **Implement dictation as a real mode.** Add an explicit state machine and
   ensure dictation text cannot be interpreted as application commands.
5. **Add Windows automation features incrementally.** Screen grids and input
   injection should have visible feedback, cancellation, and explicit
   safeguards before actions are executed.
6. **Separate policy from mechanics.** Keep transcript parsing, wake gating,
   application lookup, and OS actions in independently testable functions.

For any new automation, validate the recognized command before performing a
side effect. Speech recognition can produce incorrect text; avoid letting
untrusted transcript text run directly in PowerShell or CMD.
