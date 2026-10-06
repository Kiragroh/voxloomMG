"""Offscreen UI interaction checks and an inspectable render."""
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, Qt
from PySide6.QtTest import QTest
from PySide6.QtGui import QFontDatabase, QFont
from voxloom.ui import Window, STYLE, assets_root

app = QApplication([])
app.setStyle("Fusion")
QFontDatabase.addApplicationFont(str(assets_root() / "Inter.ttf"))
app.setFont(QFont("Inter", 10))
app.setStyleSheet(STYLE)
settings = QSettings("VoxLoom", "VoxLoom")
previous = settings.value("ui_language")
window = Window()
window.show()
app.processEvents()
assert not window.start_button.isEnabled()
fixture = Path(__file__).resolve().parents[1] / "local-test" / "Interview.wav"
window.add_files([str(fixture), str(fixture)])
assert len(window.files) == 1 and window.start_button.isEnabled()
window.ui_language.setCurrentIndex(1)
assert window.start_button.text() == "Start transcription"
window.ui_language.setCurrentIndex(0)
assert window.start_button.text() == "Transkription starten"
QTest.mouseClick(window.speakers, Qt.LeftButton)
assert not window.speaker_count.isEnabled()
QTest.mouseClick(window.speakers, Qt.LeftButton)
assert window.speaker_count.isEnabled()
window.add_files([str(fixture.parent / "not-audio.txt")])
assert window.status_key == "unsupported"
window.status_key = "ready"
window.retranslate()
app.processEvents()
out = fixture.parent
window.grab().save(str(out / "ui-de.png"))
window.ui_language.setCurrentIndex(1)
app.processEvents()
window.grab().save(str(out / "ui-en.png"))
window.clear_files()
assert not window.start_button.isEnabled()
window.close()
if previous is not None:
    settings.setValue("ui_language", previous)
else:
    settings.remove("ui_language")
print("UI interactions and DE/EN renders passed")
