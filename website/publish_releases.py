"""Create missing QuickShot GitHub Releases from catalog.js. Never deletes a release."""

import json
import os
import re
import subprocess
import urllib.error
import urllib.request

GIT = r"C:\Program Files\Git\cmd\git.exe"
REPO = "mstyleworks1234-droid/OKAWARI-Tools"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalog.js")


def token():
    filled = subprocess.run(
        [GIT, "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        check=True,
    )
    for line in filled.stdout.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    raise SystemExit("no-credential")


def api(auth, url, data=None, content_type="application/json"):
    headers = {
        "Authorization": "Bearer " + auth,
        "Accept": "application/vnd.github+json",
        "User-Agent": "okawari-release",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = None
    if data is not None and content_type == "application/json":
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = content_type
    elif data is not None:
        body = data
        headers["Content-Type"] = content_type
    request = urllib.request.Request(url, data=body, headers=headers)
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def releases():
    text = open(CATALOG, encoding="utf-8").read()
    _, _, tail = text.partition("releases: [")
    found = []
    for part in tail.split("\n        {")[1:]:
        def grab(name):
            match = re.search(r'%s:\s*"([^"]*)"' % name, part)
            return match.group(1) if match else ""
        found.append({
            "version": grab("version"),
            "fileName": grab("fileName"),
            "summary": grab("summaryJa"),
            "shaName": grab("fileName")[:-4] + ".sha256",
        })
    return found


def main():
    auth = token()
    status, payload = api(auth, "https://api.github.com/repos/%s/releases?per_page=100" % REPO)
    print("list", status)
    existing = {item["tag_name"]: item for item in json.loads(payload.decode("utf-8"))}
    for item in releases():
        tag = "quickshot-" + item["version"]
        info = existing.get(tag)
        if info is None:
            status, payload = api(auth, "https://api.github.com/repos/%s/releases" % REPO, {
                "tag_name": tag,
                "name": "QuickShot " + item["version"],
                "body": item["summary"] + "\n\n通常は最新版を使ってください。\n",
                "draft": False,
                "prerelease": False,
            })
            print("create", tag, status)
            info = json.loads(payload.decode("utf-8"))
        names = {asset["name"] for asset in info.get("assets") or []}
        upload = info.get("upload_url", "").split("{", 1)[0]
        for name in (item["fileName"], item["shaName"]):
            if name in names:
                print("keep", tag, name)
                continue
            data = open(os.path.join(ROOT, "releases", name), "rb").read()
            kind = "text/plain" if name.endswith(".sha256") else "application/octet-stream"
            status, payload = api(auth, upload + "?name=" + name, data, kind)
            print("asset", tag, name, status, len(data))


if __name__ == "__main__":
    main()
