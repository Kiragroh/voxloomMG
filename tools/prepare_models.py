"""Build-time downloads only. The shipped application never downloads anything."""
from pathlib import Path
import hashlib
import json
import tarfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "models"

def download(url, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        temporary = path.with_suffix(path.suffix + ".download")
        urllib.request.urlretrieve(url, temporary)
        temporary.replace(path)
    print(path.name, path.stat().st_size, flush=True)

def whisper():
    from huggingface_hub import HfApi, snapshot_download
    repo = "Systran/faster-whisper-small"
    pinned = ROOT / "docs" / "model-manifest.json"
    revision = json.loads(pinned.read_text(encoding="utf-8"))["sources"]["whisper"]["revision"] if pinned.exists() else HfApi().model_info(repo).sha
    snapshot_download(repo, revision=revision, local_dir=MODELS / "whisper-small", allow_patterns=["model.bin", "config.json", "tokenizer.json", "vocabulary.*", "preprocessor_config.json"])
    return {"repo": repo, "revision": revision}

def diarization():
    archive = ROOT / "build" / "segmentation.tar.bz2"
    base = "https://github.com/k2-fsa/sherpa-onnx/releases/download/"
    download(base + "speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2", archive)
    target = MODELS / "speakers"
    target.mkdir(parents=True, exist_ok=True)
    with tarfile.open(archive) as package:
        for member in package.getmembers():
            if member.isfile() and Path(member.name).name in ("model.onnx", "model.int8.onnx", "LICENSE", "README.md"):
                (target / Path(member.name).name).write_bytes(package.extractfile(member).read())
    download(base + "speaker-recongition-models/nemo_en_titanet_small.onnx", target / "embedding.onnx")
    return {"segmentation": base + "speaker-segmentation-models/sherpa-onnx-pyannote-segmentation-3-0.tar.bz2", "embedding": base + "speaker-recongition-models/nemo_en_titanet_small.onnx"}

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=2) as pool:
        w = pool.submit(whisper)
        d = pool.submit(diarization)
        sources = {"whisper": w.result(), "speakers": d.result()}
    files = {str(p.relative_to(MODELS)).replace("\\", "/"): {"size": p.stat().st_size, "sha256": hashlib.file_digest(p.open("rb"), "sha256").hexdigest()} for p in MODELS.rglob("*") if p.is_file() and ".cache" not in p.parts}
    files.pop("manifest.json", None)
    pinned = ROOT / "docs" / "model-manifest.json"
    if pinned.exists():
        expected = json.loads(pinned.read_text(encoding="utf-8"))["files"]
        if files != expected:
            raise SystemExit("Downloaded model checksums differ from the release manifest")
    (MODELS / "manifest.json").write_text(json.dumps({"sources": sources, "files": files}, indent=2), encoding="utf-8")
    print("Models ready", flush=True)
