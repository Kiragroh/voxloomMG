import json
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path
from PySide6.QtCore import QLocale, QProcess, QSettings, QStandardPaths, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QFont, QFontDatabase, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget
from .core import SUPPORTED
from .i18n import STRINGS

def app_root():
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]

def assets_root():
    return Path(getattr(sys, "_MEIPASS", app_root())) / "assets"

STYLE = """
QWidget { font-family: 'Inter'; font-size: 14px; color: #203A38; }
QMainWindow, QWidget#main { background: #F5F7F5; }
QFrame#sidebar { background: #123F3C; }
QFrame#sidebar QLabel { color: #EAF6F1; }
QLabel#sideSub { color: #A5CBC1; font-size: 12px; }
QLabel#brand { font-size: 25px; font-weight: 700; }
QLabel#hero { font-size: 31px; font-weight: 700; }
QLabel#intro, QLabel#muted { color: #687D78; }
QLabel#pill { color: #22756D; background: #E3F0E9; padding: 8px 12px; border-radius: 15px; font-size: 12px; }
QFrame#card { background: #FFFFFF; border: 1px solid #DFE8E1; border-radius: 16px; }
QLabel#section { font-weight: 700; font-size: 15px; color: #1C655F; }
QFrame#drop { background: #F0F7F3; border: 2px dashed #BDD7CC; border-radius: 13px; }
QLabel#dropTitle { font-size: 18px; font-weight: 600; }
QPushButton { background: #FFFFFF; border: 1px solid #CBDBD3; padding: 10px 16px; border-radius: 9px; font-weight: 600; }
QPushButton:hover { background: #EAF4EE; border-color: #85B7A4; }
QPushButton:pressed { background: #D4EAE0; }
QPushButton:disabled { color: #98ABA4; background: #EDF2EE; border-color: #E3EAE4; }
QPushButton#primary { background: #147C70; color: white; border: none; padding: 14px 24px; font-size: 16px; }
QPushButton#primary:hover { background: #10675D; }
QPushButton#primary:disabled { background: #B4CCC3; }
QPushButton#sideButton { color: #EAF6F1; background: transparent; border: 1px solid #416B63; text-align: left; }
QPushButton#sideButton:hover { background: #22524A; }
QComboBox, QLineEdit { background: #F8FAF8; border: 1px solid #D7E2DA; border-radius: 8px; padding: 8px 10px; min-height: 23px; }
QComboBox::drop-down { border: none; width: 25px; }
QComboBox QAbstractItemView { background: white; selection-background-color: #DDEEE5; selection-color: #203A38; }
QCheckBox { spacing: 10px; font-weight: 600; }
QCheckBox::indicator { width: 19px; height: 19px; border: 1px solid #B5CAC0; border-radius: 5px; background: white; }
QCheckBox::indicator:checked { background: #147C70; border: 4px solid #D9EEE3; }
QListWidget { border: none; background: transparent; outline: none; }
QListWidget::item { padding: 12px 8px; margin-bottom: 3px; border-radius: 8px; border-bottom: 1px solid #EEF3EF; }
QListWidget::item:selected { background: #EAF4EE; color: #203A38; }
QProgressBar { border: none; background: #E5EEE7; border-radius: 5px; height: 10px; text-align: center; }
QProgressBar::chunk { background: #29A28C; border-radius: 5px; }
"""

class DropZone(QFrame):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("drop")
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 22, 18, 22)
        self.title = QLabel()
        self.title.setObjectName("dropTitle")
        self.title.setAlignment(Qt.AlignCenter)
        self.description = QLabel()
        self.description.setObjectName("muted")
        self.description.setAlignment(Qt.AlignCenter)
        self.button = QPushButton()
        self.button.clicked.connect(owner.choose_files)
        layout.addWidget(self.title)
        layout.addWidget(self.description)
        layout.addSpacing(10)
        layout.addWidget(self.button, alignment=Qt.AlignHCenter)

    def dragEnterEvent(self, event):
        if not self.owner.busy and event.mimeData().hasUrls() and any(url.isLocalFile() for url in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.owner.add_files([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("VoxLoom", "VoxLoom")
        default_language = "de" if QLocale.system().name().startswith("de") else "en"
        self.language = self.settings.value("ui_language", default_language)
        if self.language not in STRINGS:
            self.language = "de"
        self.files = []
        self.states = []
        self.results = {}
        self.errors = {}
        self.busy = False
        self.cancelled = False
        self.buffer = b""
        self.process = None
        self.job_path = None
        self.job = None
        self.status_key = "ready"
        self.active_index = -1
        self.stage = ""
        self.setWindowTitle("VoxLoom")
        self.setWindowIcon(QIcon(str(assets_root() / "logo.png")))
        self.resize(1170, 850)
        self.setMinimumSize(1050, 790)
        self.bound_labels = []
        root = QWidget()
        self.setCentralWidget(root)
        row = QHBoxLayout(root)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        side = QFrame()
        side.setObjectName("sidebar")
        side.setFixedWidth(218)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(26, 30, 26, 24)
        logo = QLabel()
        pix = QPixmap(str(assets_root() / "logo.png"))
        logo.setPixmap(pix.scaled(88, 88, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        side_layout.addWidget(logo)
        brand = QLabel("VoxLoom")
        brand.setObjectName("brand")
        side_layout.addWidget(brand)
        tag = self.label("tagline", "sideSub")
        tag.setWordWrap(True)
        side_layout.addWidget(tag)
        side_layout.addSpacing(30)
        side_layout.addWidget(QLabel("OFFLINE STUDIO"))
        side_layout.addWidget(self.label("step1", "sideSub"))
        side_layout.addSpacing(10)
        side_layout.addWidget(self.label("step2", "sideSub"))
        side_layout.addSpacing(10)
        side_layout.addWidget(self.label("step3", "sideSub"))
        side_layout.addStretch()
        self.help_button = QPushButton()
        self.help_button.setObjectName("sideButton")
        self.help_button.clicked.connect(lambda: QMessageBox.information(self, self.t("help"), self.t("help_text")))
        side_layout.addWidget(self.help_button)
        self.about_button = QPushButton()
        self.about_button.setObjectName("sideButton")
        self.about_button.clicked.connect(lambda: QMessageBox.information(self, "VoxLoom", self.t("about_text")))
        side_layout.addWidget(self.about_button)
        side_layout.addSpacing(15)
        side_layout.addWidget(QLabel("v0.1.0", objectName="sideSub"))
        row.addWidget(side)
        main = QWidget()
        main.setObjectName("main")
        outer = QVBoxLayout(main)
        outer.setContentsMargins(34, 27, 34, 25)
        outer.setSpacing(14)
        top = QHBoxLayout()
        top.addWidget(self.label("privacy", "pill"), alignment=Qt.AlignLeft)
        top.addStretch()
        self.ui_language = QComboBox()
        self.ui_language.addItem("Deutsch", "de")
        self.ui_language.addItem("English", "en")
        self.ui_language.setCurrentIndex(0 if self.language == "de" else 1)
        self.ui_language.currentIndexChanged.connect(self.change_language)
        top.addWidget(self.ui_language)
        outer.addLayout(top)
        outer.addSpacing(4)
        outer.addWidget(self.label("hero", "hero"))
        intro = self.label("intro", "intro")
        intro.setWordWrap(True)
        outer.addWidget(intro)
        outer.addSpacing(5)
        cards = QHBoxLayout()
        cards.setSpacing(18)
        left, left_layout = self.card()
        title_row = QHBoxLayout()
        title_row.addWidget(self.label("step1", "section"))
        title_row.addStretch()
        self.file_count = QLabel()
        self.file_count.setObjectName("muted")
        title_row.addWidget(self.file_count)
        left_layout.addLayout(title_row)
        self.drop = DropZone(self)
        left_layout.addWidget(self.drop)
        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(self.item_clicked)
        self.list.setMinimumHeight(110)
        left_layout.addWidget(self.list, 1)
        self.empty = self.label("empty", "muted")
        left_layout.addWidget(self.empty)
        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self.clear_files)
        left_layout.addWidget(self.clear_button, alignment=Qt.AlignRight)
        cards.addWidget(left, 6)
        right, right_layout = self.card()
        right_layout.addWidget(self.label("step2", "section"))
        right_layout.addWidget(self.label("language", "muted"))
        self.audio_language = QComboBox()
        right_layout.addWidget(self.audio_language)
        right_layout.addSpacing(8)
        self.speakers = QCheckBox()
        self.speakers.setChecked(True)
        self.speakers.toggled.connect(self.speaker_toggle)
        right_layout.addWidget(self.speakers)
        description = self.label("speaker_help", "muted")
        description.setWordWrap(True)
        right_layout.addWidget(description)
        right_layout.addWidget(self.label("count", "muted"))
        self.speaker_count = QComboBox()
        right_layout.addWidget(self.speaker_count)
        right_layout.addSpacing(8)
        right_layout.addWidget(self.label("output", "muted"))
        self.output = QLineEdit()
        documents = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
        self.output.setText(self.settings.value("output", str(Path(documents or str(Path.home())) / "VoxLoom")))
        self.output.setReadOnly(True)
        self.output.setToolTip(self.output.text())
        right_layout.addWidget(self.output)
        self.browse_button = QPushButton()
        self.browse_button.clicked.connect(self.browse_output)
        right_layout.addWidget(self.browse_button, alignment=Qt.AlignRight)
        right_layout.addStretch()
        exports = self.label("exports", "muted")
        exports.setWordWrap(True)
        right_layout.addWidget(exports)
        cards.addWidget(right, 4)
        outer.addLayout(cards, 1)
        bottom, bottom_layout = self.card()
        self.status = QLabel()
        self.status.setWordWrap(True)
        bottom_layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setTextVisible(False)
        bottom_layout.addWidget(self.progress)
        actions = QHBoxLayout()
        self.start_button = QPushButton()
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self.start)
        actions.addWidget(self.start_button)
        self.cancel_button = QPushButton()
        self.cancel_button.clicked.connect(self.cancel)
        actions.addWidget(self.cancel_button)
        actions.addStretch()
        self.open_button = QPushButton()
        self.open_button.clicked.connect(self.open_output)
        actions.addWidget(self.open_button)
        bottom_layout.addLayout(actions)
        outer.addWidget(bottom)
        review = self.label("review", "muted")
        review.setWordWrap(True)
        outer.addWidget(review)
        row.addWidget(main, 1)
        self.retranslate()

    def t(self, key):
        return STRINGS[self.language].get(key, key)

    def label(self, key, name):
        label = QLabel()
        label.setObjectName(name)
        self.bound_labels.append((label, key))
        return label

    def card(self):
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        return frame, layout

    def change_language(self):
        self.language = self.ui_language.currentData()
        self.settings.setValue("ui_language", self.language)
        self.retranslate()

    def retranslate(self):
        for label, key in self.bound_labels:
            label.setText(self.t(key))
        for button, key in [(self.help_button, "help"), (self.about_button, "about"), (self.clear_button, "clear"), (self.browse_button, "browse"), (self.start_button, "start"), (self.cancel_button, "cancel"), (self.open_button, "open"), (self.drop.button, "choose")]:
            button.setText(self.t(key))
        self.drop.title.setText(self.t("drop"))
        self.drop.description.setText(self.t("formats"))
        self.speakers.setText(self.t("speaker_toggle"))
        audio = self.audio_language.currentData() if self.audio_language.count() else "de"
        self.audio_language.clear()
        for key, value in [("german", "de"), ("english", "en"), ("auto", "")]:
            self.audio_language.addItem(self.t(key), value)
        self.audio_language.setCurrentIndex(max(0, self.audio_language.findData(audio)))
        count = self.speaker_count.currentData() if self.speaker_count.count() else -1
        self.speaker_count.clear()
        self.speaker_count.addItem(self.t("count_auto"), -1)
        for n in range(1, 13):
            self.speaker_count.addItem(str(n), n)
        self.speaker_count.setCurrentIndex(max(0, self.speaker_count.findData(count)))
        self.refresh_list()
        self.refresh_status()
        self.update_controls()

    def refresh_list(self):
        self.list.clear()
        for i, path in enumerate(self.files):
            text = path.name + "\n" + self.t(self.states[i])
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, i)
            item.setToolTip(str(path) + ("\n" + self.t(self.errors[i]) if i in self.errors else ""))
            if self.states[i] == "done":
                item.setForeground(QColor("#147C70"))
            elif self.states[i] == "failed":
                item.setForeground(QColor("#A64B39"))
            self.list.addItem(item)
        self.empty.setVisible(not self.files)
        self.file_count.setText(self.t("count_files").format(n=len(self.files)))

    def refresh_status(self):
        if self.busy and self.stage and 0 <= self.active_index < len(self.files):
            self.status.setText(f"{self.active_index + 1}/{len(self.files)} · {self.files[self.active_index].name}\n{self.t(self.stage)}")
        else:
            self.status.setText(self.t(self.status_key))

    def speaker_toggle(self, checked):
        if hasattr(self, "speaker_count"):
            self.speaker_count.setEnabled(checked and not self.busy)

    def update_controls(self):
        self.start_button.setEnabled(bool(self.files) and not self.busy)
        self.cancel_button.setEnabled(self.busy and not self.cancelled)
        self.clear_button.setEnabled(bool(self.files) and not self.busy)
        self.drop.button.setEnabled(not self.busy)
        self.audio_language.setEnabled(not self.busy)
        self.speakers.setEnabled(not self.busy)
        self.speaker_count.setEnabled(self.speakers.isChecked() and not self.busy)
        self.browse_button.setEnabled(not self.busy)
        self.open_button.setEnabled(bool(self.results))

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, self.t("select_audio"), "", "Audio (*.wav *.mp3 *.m4a *.mp4 *.flac *.ogg *.aac *.wma *.opus *.aiff *.aif)")
        self.add_files(paths)

    def add_files(self, paths):
        if self.busy:
            return
        skipped = False
        existing = {os.path.normcase(str(p)) for p in self.files}
        for value in paths:
            path = Path(value).resolve()
            if not path.is_file() or path.suffix.lower() not in SUPPORTED:
                skipped = True
                continue
            normalized = os.path.normcase(str(path))
            if normalized not in existing:
                self.files.append(path)
                self.states.append("waiting")
                existing.add(normalized)
        self.status_key = "unsupported" if skipped else "ready"
        self.refresh_list()
        self.refresh_status()
        self.update_controls()

    def clear_files(self):
        self.files.clear()
        self.states.clear()
        self.errors.clear()
        self.status_key = "ready"
        self.progress.setValue(0)
        self.refresh_list()
        self.refresh_status()
        self.update_controls()

    def browse_output(self):
        selected = QFileDialog.getExistingDirectory(self, self.t("select_output"), self.output.text())
        if selected:
            self.output.setText(selected)
            self.output.setToolTip(selected)
            self.settings.setValue("output", selected)

    def start(self):
        if self.busy or not self.files:
            return
        from .engine import check_models
        try:
            check_models(app_root() / "models", self.speakers.isChecked())
        except Exception:
            QMessageBox.warning(self, "VoxLoom", self.t("models_missing"))
            return
        try:
            output = Path(self.output.text())
            output.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryFile(dir=output):
                pass
        except OSError:
            QMessageBox.warning(self, "VoxLoom", self.t("output_bad"))
            return
        self.results.clear()
        self.errors.clear()
        self.states = ["waiting"] * len(self.files)
        self.busy = True
        self.cancelled = False
        self.stage = "loading"
        self.active_index = 0
        self.progress.setValue(0)
        self.buffer = b""
        self.job = {"id": uuid.uuid4().hex, "files": [str(p) for p in self.files], "output": str(output), "models": str(app_root() / "models"), "options": {"language": self.audio_language.currentData(), "speakers": self.speakers.isChecked(), "speaker_count": self.speaker_count.currentData(), "ui_language": self.language}}
        fd, filename = tempfile.mkstemp(prefix="voxloom-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(self.job, handle)
        self.job_path = Path(filename)
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.SeparateChannels)
        self.process.readyReadStandardOutput.connect(self.read_events)
        self.process.readyReadStandardError.connect(lambda: self.process.readAllStandardError())
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)
        if getattr(sys, "frozen", False):
            self.process.setProgram(sys.executable)
            self.process.setArguments(["--worker", filename])
        else:
            self.process.setProgram(sys.executable)
            self.process.setArguments([str(app_root() / "launcher.py"), "--worker", filename])
        self.process.setWorkingDirectory(str(app_root()))
        self.refresh_list()
        self.refresh_status()
        self.update_controls()
        self.process.start()

    def read_events(self):
        self.buffer += bytes(self.process.readAllStandardOutput())
        while b"\n" in self.buffer:
            line, self.buffer = self.buffer.split(b"\n", 1)
            if self.cancelled:
                continue
            try:
                event = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                continue
            self.handle_event(event)

    def handle_event(self, event):
        kind = event.get("event")
        index = event.get("index", self.active_index)
        if kind == "fatal":
            for i, state in enumerate(self.states):
                if state not in ("done", "failed"):
                    self.states[i] = "failed"
                    self.errors[i] = event.get("code", "processing_failed")
        elif isinstance(index, int) and 0 <= index < len(self.files):
            if kind == "started":
                self.active_index = index
                self.states[index] = "transcribing"
            elif kind == "progress":
                self.stage = event.get("stage", "transcribing")
                self.states[index] = self.stage
                self.progress.setValue(round((index * 100 + event.get("percent", 0)) / len(self.files)))
            elif kind == "completed":
                self.states[index] = "done"
                self.results[index] = Path(event["directory"])
                self.progress.setValue(round((index + 1) * 100 / len(self.files)))
            elif kind == "failed":
                self.states[index] = "failed"
                self.errors[index] = event.get("code", "processing_failed")
        self.refresh_list()
        self.refresh_status()
        self.update_controls()

    def process_error(self, error):
        if error == QProcess.FailedToStart and self.busy:
            self.process_finished(1, QProcess.CrashExit)

    def process_finished(self, code, _status):
        if not self.busy:
            return
        self.read_events()
        for i, state in enumerate(self.states):
            if state not in ("done", "failed"):
                self.states[i] = "cancelled" if self.cancelled else "failed"
                if not self.cancelled:
                    self.errors[i] = "processing_failed"
        self.busy = False
        self.stage = ""
        self.status_key = "stopped" if self.cancelled else ("complete_errors" if self.errors else "complete")
        if not self.cancelled:
            self.progress.setValue(100)
        if self.job_path:
            self.job_path.unlink(missing_ok=True)
        if self.job:
            for i in range(len(self.files)):
                staging = Path(self.job["output"]) / (".voxloom-" + self.job["id"] + "-" + str(i))
                if staging.is_dir():
                    shutil.rmtree(staging, ignore_errors=True)
        self.process.deleteLater()
        self.refresh_list()
        self.refresh_status()
        self.update_controls()

    def cancel(self):
        if self.busy:
            self.cancelled = True
            self.status_key = "cancel_wait"
            self.stage = ""
            self.refresh_status()
            self.update_controls()
            self.process.kill()

    def item_clicked(self, item):
        index = item.data(Qt.UserRole)
        if index in self.results:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.results[index] / "Transcript.docx")))
        elif index in self.errors:
            QMessageBox.information(self, self.t("item_error"), self.t(self.errors[index]))

    def open_output(self):
        # Open the folder used by this run even if preferences change afterwards.
        folder = Path(self.job["output"]) if self.job else Path(self.output.text())
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def closeEvent(self, event):
        if self.busy:
            box = QMessageBox(self)
            box.setWindowTitle("VoxLoom")
            box.setText(self.t("confirm_close"))
            stop = box.addButton(self.t("close"), QMessageBox.AcceptRole)
            keep = box.addButton(self.t("keep"), QMessageBox.RejectRole)
            box.setDefaultButton(keep)
            box.exec()
            if box.clickedButton() != stop:
                event.ignore()
                return
            self.cancel()
            self.process.waitForFinished(5000)
            if self.busy:
                self.process_finished(1, QProcess.CrashExit)
        event.accept()

def launch():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    QFontDatabase.addApplicationFont(str(assets_root() / "Inter.ttf"))
    app.setFont(QFont("Inter", 10))
    app.setStyleSheet(STYLE)
    window = Window()
    window.show()
    return app.exec()
