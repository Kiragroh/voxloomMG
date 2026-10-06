import json
import os
import subprocess
import urllib.request

def credentials():
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="Never")
    result = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n", text=True, capture_output=True, env=env, timeout=25)
    values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
    return values.get("password")

def request(path, data=None, method=None):
    token = credentials()
    if not token:
        raise RuntimeError("No GitHub credential available in Git Credential Manager")
    headers = {"Authorization": "Bearer " + token, "Accept": "application/vnd.github+json", "User-Agent": "Transkript-build"}
    req = urllib.request.Request("https://api.github.com" + path, data=json.dumps(data).encode() if data is not None else None, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

if __name__ == "__main__":
    try:
        user = request("/user")
        print(json.dumps({"authenticated": True, "login": user["login"]}))
    except Exception as exc:
        print(json.dumps({"authenticated": False, "reason": str(exc)}))
