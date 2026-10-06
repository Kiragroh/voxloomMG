"""Maintainer command: publish the explicitly prepared portable preview to GitHub."""
import http.client
import json
from pathlib import Path
from urllib.parse import urlencode, urlparse
from github_auth_check import credentials, request

ROOT = Path(__file__).resolve().parents[1]
REPO = "Kiragroh/voxloom"
TAG = "v0.1.0"

def upload(release, path):
    matching = [asset for asset in release.get("assets", []) if asset["name"] == path.name]
    if matching:
        if matching[0]["size"] != path.stat().st_size:
            raise RuntimeError("Existing release asset differs; refusing to overwrite")
        return matching[0]
    address = urlparse(release["upload_url"].split("{")[0])
    if address.scheme != "https" or address.hostname != "uploads.github.com":
        raise RuntimeError("Unexpected upload endpoint")
    connection = http.client.HTTPSConnection(address.hostname, timeout=120)
    route = address.path + "?" + urlencode({"name": path.name})
    connection.putrequest("POST", route)
    connection.putheader("Authorization", "Bearer " + credentials())
    connection.putheader("Accept", "application/vnd.github+json")
    connection.putheader("User-Agent", "VoxLoom-release")
    connection.putheader("Content-Type", "application/zip" if path.suffix == ".zip" else "text/plain")
    connection.putheader("Content-Length", str(path.stat().st_size))
    connection.endheaders()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            connection.send(chunk)
    response = connection.getresponse()
    body = response.read()
    connection.close()
    if response.status != 201:
        raise RuntimeError(f"GitHub upload failed: HTTP {response.status}")
    return json.loads(body)

if __name__ == "__main__":
    archive = ROOT / "release" / "VoxLoom-0.1.0-Windows-x64-Portable.zip"
    checksum = ROOT / "release" / "SHA256SUMS.txt"
    if not archive.is_file() or not checksum.is_file():
        raise SystemExit("Package and checksum must exist before publishing")
    releases = request(f"/repos/{REPO}/releases")
    release = next((r for r in releases if r["tag_name"] == TAG), None)
    if release is None:
        release = request(f"/repos/{REPO}/releases", {
            "tag_name": TAG, "target_commitish": "main", "name": "VoxLoom 0.1.0 — Windows Portable",
            "draft": False, "prerelease": True,
            "body": "Voices, woven into words.\n\n**Deutsch:** Das komplette Portable-ZIP herunterladen, vollständig entpacken und VoxLoom.exe öffnen. Alle Modelle sind enthalten; kein Konto, keine Python-Installation und kein Internet erforderlich. Deutsch/Englisch, mehrere Aufnahmen, lokale Sprechertrennung sowie Word/TXT/SRT/JSON.\n\n**English:** Download and extract the complete portable ZIP, then open VoxLoom.exe. Includes models and runtime; no account, Python installation or internet required. German/English UI, file queue, offline speaker diarization, Word/TXT/SRT/JSON exports.\n\n**Preview:** Unsigned Windows 10/11 x64 application; AVX-capable CPU, preferably 8 GB RAM, about 1.5 GB disk space. Tested with synthetic recordings; see docs/VERIFICATION.md. Review automatic transcripts and speaker labels against the audio. Keep the entire folder together when sharing. Checksums, licenses, quick guides and application source are included."
        }, "POST")
    for path in (archive, checksum):
        asset = upload(release, path)
        print(json.dumps({"asset": asset["name"], "bytes": asset["size"], "url": asset["browser_download_url"], "digest": asset.get("digest")}), flush=True)
    print(json.dumps({"release": release["html_url"]}), flush=True)
