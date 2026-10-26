"""Check the static site against catalog.js and the QuickShot release files."""

import hashlib
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
PAGES = ["index.html", "quickshot.html", "about.html", "privacy.html", "terms.html"]


def fail(errors, message):
    errors.append(message)


def catalog():
    text = open(os.path.join(ROOT, "catalog.js"), encoding="utf-8").read()
    def field(name):
        match = re.search(r'%s:\s*"([^"]*)"' % name, text)
        if not match:
            raise ValueError(name)
        return match.group(1)
    return {
        "origin": field("origin"),
        "version": field("version"),
        "fileName": field("fileName"),
        "bytes": int(re.search(r"bytes:\s*(\d+)", text).group(1)),
        "sha256": field("sha256").upper(),
        "href": field("href"),
        "page": field("page"),
    }


def main():
    errors = []
    info = catalog()
    origin = info["origin"].rstrip("/")
    version_py = re.search(
        r'^VERSION = "([^"]+)"',
        open(os.path.join(REPO, "quickshot", "main.py"), encoding="utf-8").read(),
        re.M,
    ).group(1)
    version_ext = re.search(
        r'"version": "([^"]+)"',
        open(os.path.join(REPO, "quickshot", "extension", "manifest.json"), encoding="utf-8").read(),
    ).group(1)
    if info["version"] != version_py or info["version"] != version_ext:
        fail(errors, "version mismatch catalog=%s app=%s extension=%s" % (info["version"], version_py, version_ext))
    exe = os.path.join(REPO, "releases", info["fileName"])
    if not os.path.isfile(exe):
        fail(errors, "missing " + exe)
    else:
        data = open(exe, "rb").read()
        digest = hashlib.sha256(data).hexdigest().upper()
        if len(data) != info["bytes"] or digest != info["sha256"]:
            fail(errors, "EXE size or SHA-256 does not match catalog.js")
        sha_file = open(exe[:-4] + ".sha256", encoding="ascii").read().split()[0].upper()
        if sha_file != digest:
            fail(errors, "sha256 file does not match the EXE")
    if info["fileName"] not in info["href"] or "github.com/" not in info["href"]:
        fail(errors, "download URL is not a GitHub release asset")
    quickshot = open(os.path.join(ROOT, "quickshot.html"), encoding="utf-8").read()
    if info["version"] not in quickshot:
        fail(errors, "quickshot.html does not show the catalog version")
    robots = open(os.path.join(ROOT, "robots.txt"), encoding="utf-8").read()
    if origin + "/sitemap.xml" not in robots:
        fail(errors, "robots.txt does not point at the sitemap")
    sitemap = open(os.path.join(ROOT, "sitemap.xml"), encoding="utf-8").read()
    expected = [origin + "/"] + [origin + "/" + name for name in PAGES if name != "index.html"]
    for url in expected:
        if "<loc>%s</loc>" % url not in sitemap:
            fail(errors, "sitemap missing " + url)
    for name in PAGES:
        html = open(os.path.join(ROOT, name), encoding="utf-8").read()
        if "<title>" not in html or 'name="description"' not in html or 'rel="canonical"' not in html:
            fail(errors, name + " is missing title, description, or canonical")
        if "catalog.js" not in html or "app.js" not in html:
            fail(errors, name + " is missing a site script")
        for href in re.findall(r'href="([^"]+)"', html):
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = href.split("#", 1)[0].split("?", 1)[0]
            if target and not os.path.exists(os.path.join(ROOT, target)):
                fail(errors, "%s links to missing %s" % (name, href))
    if errors:
        print("\n".join(errors))
        return 1
    print("site check ok %s" % info["version"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
