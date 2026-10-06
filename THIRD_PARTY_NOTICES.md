# Third-party components and model weights

VoxLoom source is MIT licensed. Dependencies and weights retain their original terms. License texts collected from installed distributions and upstreams are included in the portable package under `licenses/`.

| Component | Upstream | License |
| --- | --- | --- |
| faster-whisper 1.2.1 | https://github.com/SYSTRAN/faster-whisper | MIT |
| Whisper small weights | https://github.com/openai/whisper, converted by https://huggingface.co/Systran/faster-whisper-small | MIT |
| CTranslate2 4.8.2 | https://github.com/OpenNMT/CTranslate2 | MIT |
| sherpa-onnx 1.13.8 | https://github.com/k2-fsa/sherpa-onnx | Apache-2.0 |
| Pyannote segmentation 3.0, quantized ONNX | https://huggingface.co/pyannote/segmentation-3.0, converted by sherpa-onnx | MIT, Copyright 2022 CNRS (license included with model archive) |
| NVIDIA TitaNet Small, ONNX conversion | https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemo/models/titanet_small | NeMo Toolkit Apache-2.0, as specified in the model's license section |
| Silero VAD packaged in faster-whisper | https://github.com/snakers4/silero-vad | MIT |
| PySide6 / Shiboken6 / Qt 6.11.2 | https://www.qt.io/qt-for-python | LGPLv3 (also GPL/commercial options upstream) |
| Inter font | https://github.com/google/fonts/tree/main/ofl/inter | SIL Open Font License 1.1 |
| PyAV 18.1.0 | https://github.com/PyAV-Org/PyAV | BSD-3-Clause |
| FFmpeg libraries bundled by PyAV | https://ffmpeg.org, https://github.com/PyAV-Org/pyav-ffmpeg | The pinned Windows wheel reports LGPL version 3 or later; supporting libraries retain their own licenses |
| python-docx 1.2.0 | https://github.com/python-openxml/python-docx | MIT |
| NumPy, ONNX Runtime, Tokenizers, lxml, Python and supporting libraries | See their installed-distribution licenses | See `licenses/` |

The TitaNet Small model is converted to ONNX by sherpa-onnx; see https://github.com/k2-fsa/sherpa-onnx/blob/master/scripts/nemo/speaker-verification/export-onnx.py for the conversion. The segmentation model is distributed as an INT8 conversion. Original model publishers do not endorse VoxLoom. Model download URLs, exact Whisper revision, byte sizes and checksums are recorded in the model manifest.

## Qt / LGPL information

Qt and PySide6 are dynamically linked. The `.dll` and `.pyd` files are in `_internal/PySide6` and `_internal/shiboken6`; the executable does not statically embed these libraries. You may replace these shared libraries with compatible modified versions. Reverse engineering for debugging modifications to the LGPL libraries is permitted. VoxLoom's full application source is included as `VoxLoom-source.zip`; build instructions are in README.md. No changes were made to Qt or PySide6 itself.

Corresponding upstream source and build instructions:

- Qt 6.11.2: https://download.qt.io/official_releases/qt/6.11/6.11.2/ and https://code.qt.io/cgit/qt/
- PySide6/Shiboken6 6.11.2: https://download.qt.io/official_releases/QtForPython/pyside6/ and https://code.qt.io/cgit/pyside/pyside-setup.git/
- Qt for Python build guide: https://doc.qt.io/qtforpython-6/building_from_source/index.html
- LGPLv3 text and GPLv3 referenced by it: included in `licenses/`.

## FFmpeg / PyAV build information

The unmodified PyAV Windows wheel bundles FFmpeg libraries and supporting codecs. The actual bundled `avcodec_license()` reports "LGPL version 3 or later". Upstream build source and configuration are maintained by PyAV at https://github.com/PyAV-Org/pyav-ffmpeg and https://github.com/PyAV-Org/PyAV. The build configuration used by the pinned wheel is included in `licenses/FFmpeg-wheel-build.txt`. See the FFmpeg COPYING files for the applicable terms; these libraries remain separable shared binaries in `_internal/av.libs`.

## Brand asset

The VoxLoom logo was generated with the built-in GPT Image tool for this application. Its generation prompt and provenance are recorded in `docs/branding.json`. The logo and application icon are included as project assets; they are not a logo of any upstream project.
