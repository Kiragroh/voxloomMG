"""Save full upstream notices for the redistributable package."""
from pathlib import Path
import urllib.request
ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "whisper-MIT.txt": "https://raw.githubusercontent.com/openai/whisper/main/LICENSE",
    "nemo-Apache-2.0.txt": "https://raw.githubusercontent.com/NVIDIA/NeMo/main/LICENSE",
    "sherpa-onnx-Apache-2.0.txt": "https://raw.githubusercontent.com/k2-fsa/sherpa-onnx/master/LICENSE",
    "silero-vad-MIT.txt": "https://raw.githubusercontent.com/snakers4/silero-vad/master/LICENSE",
    "Qt-LGPL-3.0.txt": "https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/LGPL-3.0-only.txt",
    "Qt-GPL-3.0.txt": "https://raw.githubusercontent.com/qt/qtbase/v6.11.2/LICENSES/GPL-3.0-only.txt",
    "FFmpeg-LGPL-2.1.txt": "https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.LGPLv2.1",
    "FFmpeg-LGPL-3.txt": "https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.LGPLv3",
    "FFmpeg-GPL-2.txt": "https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.GPLv2",
    "FFmpeg-GPL-3.txt": "https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/COPYING.GPLv3",
    "FFmpeg-license-notes.md": "https://raw.githubusercontent.com/FFmpeg/FFmpeg/master/LICENSE.md",
    "Python-license.txt": "https://raw.githubusercontent.com/python/cpython/v3.11.7/LICENSE",
}
if __name__ == "__main__":
    directory = ROOT / "licenses"
    directory.mkdir(exist_ok=True)
    for filename, url in SOURCES.items():
        with urllib.request.urlopen(url, timeout=30) as response:
            (directory / filename).write_bytes(response.read())
        print(filename)
