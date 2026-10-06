# Release verification — 0.1.0

Verified on 2026-10-06 on Windows x64, AMD Ryzen 7 5800X, approximately 51 GB RAM. Built with Python 3.11.7 and the versions in `requirements-lock.txt`.

## Passed locally

- Six unit tests: speaker-to-word alignment, unknown/ambiguous assignments, preserving repeated speech, paragraph limits, long timestamps, Windows-safe output names and Unicode/DE/EN exports.
- Source and final frozen EXE GUI integration: a German two-speaker recording, Word and other exports, recovery after a corrupt recording in the same batch, a second run without changing the original output, cancellation and temporary-file cleanup, and German/English interface switching.
- Final frozen EXE: German MP3 with a Unicode filename (`Gespräch Ärztin.mp3`) and two speakers; English WAV without diarization. Exports inspected as JSON and opened through python-docx.
- The MP3 and English checks ran from a different working directory with only Windows system directories on PATH, with no Python on PATH. The EXE used bundled runtime libraries and models.
- Python socket connection and DNS APIs were made to raise exceptions during these frozen engine checks. Inference and all exports completed. This is an application-level offline check, not a packet capture or a Windows firewall audit.
- German test speech contained a female voice and a male voice, generated locally with Windows speech synthesis. English test speech was also synthetic. No real interview, mail content or personal transcript is shipped.

## Build details

An initial build accidentally collected a Poppler ICU DLL from the developer machine's PATH. This DLL prevented Qt startup. The build script now gives PyInstaller a minimal Windows/Python PATH and bundles the matching Qt MSVC runtime. The final clean build passed the GUI and frozen inference checks above.

Models are pinned with file hashes in `docs/model-manifest.json`. The package includes their weights, license notices, quick guides and the full application source. The portable ZIP has a SHA256 checksum in the release assets.

## Limits

This is an unsigned preview. It has not been tested in a clean Windows virtual machine, on institutional managed PCs, or on representative long/noisy/overlapping research interviews. The tested machine has more RAM than a typical laptop. Audio is decoded in memory, so long recordings require additional RAM; decoding and diarization may take time before the progress value advances. No production accuracy or speed benchmark is claimed. Transcripts and speaker labels require listening and review; paragraph-based SRT output is an editable starting point.

## Repeating checks

Run `python -m pytest -q` after installing the locked requirements. `tools/gui_integration.py` is exercised through `launcher.py --smoke-ui <test-folder>` or `VoxLoom.exe --smoke-ui <test-folder>`; the folder must contain synthetic `Interview-DE.wav` with the phrases asserted by that script, plus `invalid.wav`. The synthetic fixture audio is deliberately not distributed. To check your own audio without the GUI:

```powershell
.\VoxLoom.exe --verify "C:\Test\recording.wav" --output "C:\Test\results" --language de --speaker-count 2 --block-network
```

Inspect stdout JSON events for `completed` or `failed`. These command-line verification events are not persistent application logs.
