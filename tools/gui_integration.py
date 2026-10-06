"""Used with --smoke-ui to test the source and frozen application through its GUI."""
import json
import time
from pathlib import Path
from PySide6.QtCore import QEventLoop
from voxloom.ui import Window

def wait(app, predicate, timeout=90):
    start = time.monotonic()
    while not predicate():
        app.processEvents(QEventLoop.AllEvents, 100)
        if time.monotonic() - start > timeout:
            raise AssertionError("GUI operation timed out")
        time.sleep(0.02)

def run(app, directory):
    directory = Path(directory).resolve()
    window = Window()
    window.show()
    window.ui_language.setCurrentIndex(1)
    window.add_files([str(directory / "Interview-DE.wav"), str(directory / "invalid.wav")])
    window.audio_language.setCurrentIndex(0)
    window.speaker_count.setCurrentIndex(window.speaker_count.findData(2))
    window.output.setText(str(directory / "gui-results"))
    window.start()
    wait(app, lambda: not window.busy)
    assert window.states == ["done", "failed"], window.states
    assert window.status_key == "complete_errors"
    assert window.open_button.isEnabled()
    result = window.results[0]
    data = json.loads((result / "Transcript.json").read_text(encoding="utf-8"))
    assert {turn["speaker"] for turn in data["turns"]} == {"1", "2"}
    assert "Krankenhaus" in " ".join(turn["text"] for turn in data["turns"])
    assert "Speaker 1" in (result / "Transcript.txt").read_text(encoding="utf-8-sig")
    assert "Patientinnen" in " ".join(turn["text"] for turn in data["turns"])
    # Retry must create a new folder, leaving the first transcript untouched.
    first_bytes = (result / "Transcript.docx").read_bytes()
    window.clear_files()
    window.add_files([str(directory / "Interview-DE.wav")])
    window.start()
    wait(app, lambda: not window.busy)
    assert window.states == ["done"]
    assert window.results[0] != result
    assert (result / "Transcript.docx").read_bytes() == first_bytes
    # Cancellation while the worker is active must return control and remove staging.
    window.start()
    assert window.busy
    window.cancel()
    wait(app, lambda: not window.busy, timeout=10)
    assert window.status_key == "stopped"
    assert not list((directory / "gui-results").glob(".voxloom-*"))
    assert window.job_path is None or not window.job_path.exists()
    window.ui_language.setCurrentIndex(0)
    window.grab().save(str(directory / "gui-tested-de.png"))
    window.ui_language.setCurrentIndex(1)
    window.grab().save(str(directory / "gui-tested-en.png"))
    window.close()
    print(json.dumps({"gui_test": "passed", "checks": ["worker subprocess", "two speakers", "Word export", "bad-file recovery", "non-destructive rerun", "cancel", "DE/EN"]}), flush=True)
