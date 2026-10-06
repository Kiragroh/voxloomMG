import json
import urllib.error
from github_auth_check import request

if __name__ == "__main__":
    name = "voxloom"
    user = request("/user")
    try:
        existing = request(f"/repos/{user['login']}/{name}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    else:
        raise SystemExit("Repository already exists; refusing to replace it")
    repo = request("/user/repos", {"name": name, "private": True, "description": "VoxLoom — portable offline transcription with German/English UI, local speaker detection and Word export", "has_issues": True, "has_wiki": False, "auto_init": False})
    print(json.dumps({"url": repo["html_url"], "clone_url": repo["clone_url"], "private": repo["private"]}))
