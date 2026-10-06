"""Repeatable portable build; model files stay outside the executable."""
import json
from pathlib import Path
import subprocess
import sys
import shutil
import os
ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    # A developer machine's Poppler/Conda tools may expose a different icuuc.dll
    # on PATH. Qt links to the Windows ICU API; collecting that unrelated DLL
    # produces a broken executable. Build against Python and Windows paths only.
    env = dict(os.environ)
    windows = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    env["PATH"] = os.pathsep.join([str(Path(sys.executable).parent), str(Path(sys.base_prefix)), str(windows / "System32"), str(windows)])
    subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--onedir", "--console", "--hide-console", "hide-early", "--name", "VoxLoom", "--icon", str(ROOT / "assets" / "logo.ico"), "--add-data", str(ROOT / "assets") + ";assets", "--collect-all", "faster_whisper", "--collect-all", "ctranslate2", "--collect-all", "sherpa_onnx", "--collect-all", "sherpa_onnx_core", "--collect-all", "onnxruntime", "--collect-all", "av", "--exclude-module", "torch", "--exclude-module", "tensorflow", "--exclude-module", "matplotlib", "--exclude-module", "pytest", str(ROOT / "launcher.py")], cwd=ROOT, env=env, check=True)
    # Ship the matching MSVC runtime from Qt instead of requiring installation.
    runtime = ROOT / "dist" / "VoxLoom" / "_internal"
    for dll in (runtime / "PySide6").glob("*140*.dll"):
        shutil.copy2(dll, runtime / dll.name)
