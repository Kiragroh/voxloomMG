# VoxLoom

<img src="assets/logo.png" width="112" alt="VoxLoom logo">

**Voices, woven into words.** A portable Windows application for private, offline interview transcription. English and German interface. Built from an earlier research transcription workflow by Max Grohmann.

## For users / Für Anwender:innen

1. Download `VoxLoom-0.1.0-Windows-x64-Portable.zip` and **extract the entire ZIP**.
2. Open `VoxLoom.exe` inside the extracted folder.
3. Drop recordings into the window, choose the recording language and speaker count, then start.
4. Open the results folder. Each recording receives a separate folder with Word, TXT, SRT and JSON exports.

**Deutsch:** ZIP vollständig entpacken → `VoxLoom.exe` öffnen → Aufnahmen auswählen → Transkription starten. Die Oberfläche lässt sich oben rechts zwischen Deutsch und Englisch umschalten. Bitte die EXE zusammen mit den Ordnern `_internal` und `models` lassen.

No Python, FFmpeg installation, GPU, account, API key or internet connection is needed. The complete speech and speaker models are included. The application never downloads models, uploads recordings or checks for updates. Original audio files remain untouched. Interface language and destination preference are stored locally in Windows settings; interviews are not saved there.

## Features

- Clear DE/EN interface, drag and drop, multi-file queue, progress and immediate cancellation.
- German, English or automatic recording-language detection (per file; choose the actual recording language for best results).
- Faster Whisper `small`, CPU INT8, silence filtering and word timestamps.
- Local speaker diarization: Pyannote segmentation ONNX + NeMo TitaNet embedding via sherpa-onnx. Choose the known speaker count or automatic clustering.
- Word paragraphs with times and neutral speaker labels; uncertain assignments are marked `*`.
- Collision-safe output folders and atomic export publication; reruns never append duplicate transcript text.
- One bad recording does not stop the rest of the queue. Cancellation keeps completed transcripts.
- GPT Image logo, bundled Inter font, Windows icon.

Automatic transcription is a first draft. Please check omissions, technical terms, speaker labels and overlapping speech while listening. Speaker labels are anonymous clusters within one recording; they do not identify people. The subtitle export follows transcript paragraphs and is intended as an editable starting point.

## Windows requirements

Windows 10/11 x64, a CPU supporting AVX (required by the inference runtime), and preferably at least 8 GB RAM. Allow roughly 1.5 GB free disk space to extract the full package; long recordings need additional memory and output space. No admin rights are needed by the app. This preview is unsigned; Windows or institutional application policies may require approval to run an unfamiliar executable. There is no instruction to disable security protections.

## Development

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe tools/prepare_models.py
.\.venv\Scripts\python.exe launcher.py
```

Downloads happen only in the explicit developer command `prepare_models.py`. It records model repository revisions, byte sizes and SHA256 hashes in `models/manifest.json`. The pinned download sources for this release are also recorded in `docs/model-manifest.json`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe tools/build.py
.\.venv\Scripts\python.exe tools/package.py
```

The portable ZIP contains the executable, shared runtime libraries, models, licenses, quick guide and a source archive. A folder build avoids unpacking a half-gigabyte speech model every time the application starts. Send the **complete ZIP**, not just the EXE. See `docs/VERIFICATION.md` for the checks actually performed.

## Architecture

`voxloom/ui.py` owns the GUI and starts a separate process. `engine.py` loads models once per batch and sends JSON progress events. Killing this process cancels inference without freezing the GUI. `core.py` aligns speaker intervals to individual words instead of assigning whole Whisper segments to one person. `export.py` writes all files in a staging folder before atomically publishing the results.

## License and acknowledgements

Application source: MIT. Bundled components and model weights retain their own licenses; see `THIRD_PARTY_NOTICES.md` and `licenses/` in the portable package. Qt/PySide6 is dynamically linked under LGPLv3; the package includes application source, Qt licensing information and instructions for replacing the libraries. No medical recordings, personal transcripts, legacy access tokens or mail contents are included in the repository or release.
