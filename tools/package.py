from pathlib import Path
import hashlib
import importlib.metadata
import json
import shutil
import zipfile
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
VERSION = "0.1.0"

def allowed_source(path):
    return not any(part in {".git", ".venv", "__pycache__", ".pytest_cache", "models", "build", "dist", "release", "local-reference", "local-test"} for part in path.relative_to(ROOT).parts) and path.suffix not in {".log", ".spec"}

if __name__ == "__main__":
    from voxloom.engine import check_models
    check_models(ROOT / "models", True)
    target = ROOT / "dist" / "VoxLoom"
    if not (target / "VoxLoom.exe").is_file():
        raise SystemExit("Build the Windows executable first")
    shutil.copytree(ROOT / "models", target / "models", dirs_exist_ok=True, ignore=shutil.ignore_patterns(".cache", "*.download"))
    for name in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(ROOT / name, target / name)
    for name in ("QUICKSTART-DE.txt", "QUICKSTART-EN.txt"):
        shutil.copy2(ROOT / "docs" / name, target / name)
    license_root = target / "licenses"
    license_root.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "assets" / "Inter-OFL.txt", license_root / "Inter-OFL.txt")
    shutil.copytree(ROOT / "licenses", license_root, dirs_exist_ok=True)
    shutil.copy2(ROOT / "models" / "speakers" / "LICENSE", license_root / "pyannote-segmentation-MIT.txt")
    for dist in importlib.metadata.distributions():
        name = dist.metadata["Name"]
        for file in dist.files or []:
            if ".dist-info" in str(file) and file.suffix not in {".pyc", ".py"} and any(term in str(file).lower() for term in ("license", "copying", "notice")):
                origin = dist.locate_file(file)
                if origin.is_file():
                    folder = license_root / name
                    folder.mkdir(exist_ok=True)
                    shutil.copy2(origin, folder / origin.name)
    (ROOT / "release").mkdir(exist_ok=True)
    source = target / "VoxLoom-source.zip"
    with zipfile.ZipFile(source, "w", zipfile.ZIP_DEFLATED) as z:
        for path in ROOT.rglob("*"):
            if path.is_file() and allowed_source(path):
                z.write(path, path.relative_to(ROOT))
    archive = ROOT / "release" / f"VoxLoom-{VERSION}-Windows-x64-Portable.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in target.rglob("*"):
            if path.is_file():
                z.write(path, Path("VoxLoom") / path.relative_to(target))
    digest = hashlib.file_digest(archive.open("rb"), "sha256").hexdigest()
    checksum = archive.parent / "SHA256SUMS.txt"
    checksum.write_text(digest + "  " + archive.name + "\n", encoding="ascii")
    print(json.dumps({"archive": str(archive), "bytes": archive.stat().st_size, "sha256": digest}))
