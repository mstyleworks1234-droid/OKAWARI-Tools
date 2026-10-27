"""Refresh the profile's latest note articles and YouTube videos.

note uses the public RSS feed. YouTube uses the public channel Atom feed.
Each source is fetched on its own. A failed source keeps its previous items.
Files are written only when the saved items change. No API key is used.
"""

import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "website" / "activity.json"
PAGE_PATH = ROOT / "website" / "profile.html"

NOTE_FEED = "https://note.com/okawariojisan/rss"
NOTE_PROFILE = "https://note.com/okawariojisan"
YOUTUBE_PROFILE = "https://www.youtube.com/@okawariojisan2gou"
YOUTUBE_CHANNEL_ID = "UCzPd5Bn2S_Mtt4tqHKKq7dA"
YOUTUBE_FEED = "https://www.youtube.com/feeds/videos.xml?channel_id=" + YOUTUBE_CHANNEL_ID
YOUTUBE_VIDEOS = YOUTUBE_PROFILE + "/videos"
USER_AGENT = "Mozilla/5.0 (compatible; OKAWARI-Tools/1.0; +https://okawari-tools.com/profile)"
BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
LIMIT = 3
JST = timezone(timedelta(hours=9))

NOTE_URL = re.compile(r"^https://note\.com/okawariojisan/n/n[0-9a-f]+$")
VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
ATOM = {"a": "http://www.w3.org/2005/Atom", "y": "http://www.youtube.com/xml/schemas/2015"}


def fetch_bytes(url, browser=False):
    headers = {
        "User-Agent": BROWSER if browser else USER_AGENT,
        "Accept-Language": "ja",
        "Accept": "text/html,application/xhtml+xml" if browser else "application/atom+xml, application/xml, text/xml, */*",
    }
    request = urllib.request.Request(url, headers=headers)
    delay = 1
    last_error = None
    for _ in range(4):
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise
            last_error = error
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            last_error = error
        time.sleep(delay)
        delay *= 2
    raise last_error


def clean_summary(value, title):
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text or text == title:
        return ""
    if len(text) > 80:
        text = text[:80].rstrip() + "…"
    return text


def select_items(items):
    newest = {}
    for item in items:
        current = newest.get(item["url"])
        if current is None or item["published"] > current["published"]:
            newest[item["url"]] = item
    ordered = sorted(newest.values(), key=lambda item: item["published"], reverse=True)
    return ordered[:LIMIT]


def parse_note(payload):
    root = ET.fromstring(payload)
    channel_link = root.findtext("./channel/link") or ""
    if not channel_link.startswith(NOTE_PROFILE):
        return None
    found = []
    for item in root.findall("./channel/item"):
        title = re.sub(r"\s+", " ", (item.findtext("title") or "")).strip()
        url = (item.findtext("link") or "").strip()
        published_raw = (item.findtext("pubDate") or "").strip()
        if not title or not NOTE_URL.match(url) or not published_raw:
            continue
        published = parsedate_to_datetime(published_raw).astimezone(JST).isoformat(timespec="seconds")
        entry = {"title": title, "url": url, "published": published}
        summary = clean_summary(item.findtext("description") or "", title)
        if summary:
            entry["summary"] = summary
        found.append(entry)
    return select_items(found) or None


def parse_youtube(payload):
    root = ET.fromstring(payload)
    channel_id = root.findtext("y:channelId", namespaces=ATOM)
    if channel_id != YOUTUBE_CHANNEL_ID:
        return None
    found = []
    for entry in root.findall("a:entry", ATOM):
        title = re.sub(r"\s+", " ", (entry.findtext("a:title", namespaces=ATOM) or "")).strip()
        video_id = (entry.findtext("y:videoId", namespaces=ATOM) or "").strip()
        published_raw = (entry.findtext("a:published", namespaces=ATOM) or "").strip()
        if not title or not VIDEO_ID.match(video_id) or not published_raw:
            continue
        published = datetime.fromisoformat(published_raw.replace("Z", "+00:00")).astimezone(JST).isoformat(timespec="seconds")
        found.append({
            "title": title,
            "url": "https://www.youtube.com/watch?v=" + video_id,
            "published": published,
            "thumbnail": "https://i.ytimg.com/vi/" + video_id + "/mqdefault.jpg",
        })
    return select_items(found) or None


def json_string(value):
    return json.loads('"%s"' % value)


def video_published(video_id):
    page = fetch_bytes("https://www.youtube.com/watch?v=" + video_id, browser=True).decode("utf-8", "replace")
    match = re.search(r'itemprop="datePublished" content="([^"]+)"', page)
    if not match or YOUTUBE_CHANNEL_ID not in page:
        return ""
    return datetime.fromisoformat(match.group(1)).astimezone(JST).isoformat(timespec="seconds")


def parse_youtube_page(payload):
    text = payload.decode("utf-8", "replace")
    if YOUTUBE_CHANNEL_ID not in text:
        return None
    pattern = re.compile(
        r'"lockupMetadataViewModel":\{"title":\{"content":"((?:\\.|[^"\\])*)"\}'
        r'.{0,12000}?"videoId":"([A-Za-z0-9_-]{11})"',
        re.S,
    )
    found = []
    seen = set()
    for match in pattern.finditer(text):
        video_id = match.group(2)
        if video_id in seen or not VIDEO_ID.match(video_id):
            continue
        seen.add(video_id)
        title = re.sub(r"\s+", " ", json_string(match.group(1))).strip()
        if not title:
            continue
        try:
            published = video_published(video_id)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError):
            continue
        if not published:
            continue
        found.append({
            "title": title,
            "url": "https://www.youtube.com/watch?v=" + video_id,
            "published": published,
            "thumbnail": "https://i.ytimg.com/vi/" + video_id + "/mqdefault.jpg",
        })
        if len(found) == LIMIT:
            break
    return select_items(found) or None


def load_youtube():
    try:
        parsed = parse_youtube(fetch_bytes(YOUTUBE_FEED))
        if parsed:
            return parsed, "feed"
    except (urllib.error.URLError, TimeoutError, OSError, ET.ParseError):
        pass
    try:
        parsed = parse_youtube_page(fetch_bytes(YOUTUBE_VIDEOS, browser=True))
        if parsed:
            return parsed, "public-page"
    except (urllib.error.URLError, TimeoutError, OSError, ET.ParseError):
        pass
    return None, "unavailable"


def load_previous():
    if not DATA_PATH.is_file():
        return empty_data()
    try:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return empty_data()
    note_items = data.get("note", {}).get("items")
    youtube_items = data.get("youtube", {}).get("items")
    return {
        "note": {"profile": NOTE_PROFILE, "items": note_items if isinstance(note_items, list) else []},
        "youtube": {
            "profile": YOUTUBE_PROFILE,
            "channel_id": YOUTUBE_CHANNEL_ID,
            "items": youtube_items if isinstance(youtube_items, list) else [],
        },
        "updated": data.get("updated") or "",
    }


def empty_data():
    return {
        "note": {"profile": NOTE_PROFILE, "items": []},
        "youtube": {"profile": YOUTUBE_PROFILE, "channel_id": YOUTUBE_CHANNEL_ID, "items": []},
        "updated": "",
    }


def source_items(data, name):
    return data.get(name, {}).get("items") or []


def merge(previous, note_items, youtube_items):
    data = empty_data()
    data["note"]["items"] = source_items(previous, "note") if note_items is None else note_items
    data["youtube"]["items"] = source_items(previous, "youtube") if youtube_items is None else youtube_items
    data["updated"] = previous.get("updated") or ""
    return data


def items_changed(previous, data):
    return source_items(previous, "note") != data["note"]["items"] or source_items(previous, "youtube") != data["youtube"]["items"]


def render_note(items):
    if not items:
        return '            <li><p class="activity-empty" data-i18n="profile_activity_empty">新着はまだありません。</p></li>'
    blocks = []
    for item in items:
        summary = ""
        if item.get("summary"):
            summary = '<span class="activity-summary">%s</span>' % html.escape(item["summary"])
        blocks.append(
            "            <li><a href=\"%s\" target=\"_blank\" rel=\"noopener noreferrer\">"
            "<span class=\"activity-date\">%s</span>"
            "<span class=\"activity-title\">%s</span>%s</a></li>"
            % (html.escape(item["url"], quote=True), html.escape(item["published"][:10]), html.escape(item["title"]), summary)
        )
    return "\n".join(blocks)


def render_youtube(items):
    if not items:
        return '            <li><p class="activity-empty" data-i18n="profile_activity_empty">新着はまだありません。</p></li>'
    blocks = []
    for item in items:
        blocks.append(
            "            <li><a href=\"%s\" target=\"_blank\" rel=\"noopener noreferrer\">"
            "<img src=\"%s\" alt=\"\" width=\"320\" height=\"180\" loading=\"lazy\" decoding=\"async\" referrerpolicy=\"no-referrer\">"
            "<span class=\"activity-date\">%s</span>"
            "<span class=\"activity-title\">%s</span></a></li>"
            % (
                html.escape(item["url"], quote=True),
                html.escape(item["thumbnail"], quote=True),
                html.escape(item["published"][:10]),
                html.escape(item["title"]),
            )
        )
    return "\n".join(blocks)


def replace_block(page, name, inner):
    pattern = re.compile(r"(<!-- activity:%s -->).*?(<!-- /activity:%s -->)" % (name, name), re.S)
    if len(pattern.findall(page)) != 1:
        raise RuntimeError("activity marker missing: " + name)
    return pattern.sub(lambda match: match.group(1) + "\n" + inner + "\n            " + match.group(2), page, count=1)


def render_page(page, data, updated):
    page = replace_block(page, "note", render_note(data["note"]["items"]))
    page = replace_block(page, "youtube", render_youtube(data["youtube"]["items"]))
    display = datetime.fromisoformat(updated).astimezone(JST).strftime("%Y-%m-%d %H:%M JST")
    replaced, count = re.subn(
        r'(<time id="activity-updated" datetime=")[^"]*(">)[^<]*(</time>)',
        lambda match: match.group(1) + updated + match.group(2) + display + match.group(3),
        page,
        count=1,
    )
    if count != 1:
        raise RuntimeError("activity timestamp missing")
    return replaced


def write_outputs(data):
    updated = datetime.now(JST).isoformat(timespec="seconds")
    data["updated"] = updated
    page = PAGE_PATH.read_text(encoding="utf-8")
    rendered = render_page(page, data, updated)
    DATA_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PAGE_PATH.write_text(rendered, encoding="utf-8")


def update():
    previous = load_previous()
    note_items = None
    youtube_items = None
    note_error = ""
    youtube_error = ""
    try:
        note_items = parse_note(fetch_bytes(NOTE_FEED))
        if note_items is None:
            note_error = "note feed was empty or unexpected"
    except (urllib.error.URLError, TimeoutError, OSError, ET.ParseError) as error:
        note_error = type(error).__name__
    youtube_items, youtube_detail = load_youtube()
    if youtube_items is None:
        youtube_error = youtube_detail
    data = merge(previous, note_items, youtube_items)
    changed = items_changed(previous, data)
    if changed:
        write_outputs(data)
    report(data, note_error, youtube_error, youtube_detail, changed)
    return 0


def report(data, note_error, youtube_error, youtube_detail, changed):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print("note", "kept-previous" if note_error else "ok", len(data["note"]["items"]), note_error)
    for item in data["note"]["items"]:
        print("-", item["published"][:10], item["title"])
    print("youtube", "kept-previous" if youtube_error else "ok", len(data["youtube"]["items"]), youtube_error or youtube_detail)
    for item in data["youtube"]["items"]:
        print("-", item["published"][:10], item["title"])
    print("changed", "yes" if changed else "no")


def self_test():
    escaped = html.escape('<script>alert("x")</script>')
    assert "&lt;script&gt;" in escaped
    assert NOTE_URL.match("https://note.com/okawariojisan/n/nbe72e851daed")
    assert not NOTE_URL.match("https://example.com/okawariojisan/n/nbe72e851daed")
    assert not NOTE_URL.match("https://note.com/okawariojisan")
    assert VIDEO_ID.match("abcdefghijk")
    assert not VIDEO_ID.match("short")
    assert not VIDEO_ID.match("abcdefghijk<script>")
    older = {"title": "old", "url": "https://note.com/okawariojisan/n/naaaaaaaaaaaa", "published": "2025-01-01T00:00:00+09:00"}
    newer = {"title": "new", "url": "https://note.com/okawariojisan/n/nbbbbbbbbbbb", "published": "2025-02-01T00:00:00+09:00"}
    duplicate = {"title": "new copy", "url": newer["url"], "published": "2025-01-15T00:00:00+09:00"}
    selected = select_items([older, newer, duplicate, {"title": "mid", "url": "https://note.com/okawariojisan/n/nccccccccccc", "published": "2025-01-20T00:00:00+09:00"}, {"title": "extra", "url": "https://note.com/okawariojisan/n/nddddddddddd", "published": "2024-12-01T00:00:00+09:00"}])
    assert [item["title"] for item in selected] == ["new", "mid", "old"]
    assert clean_summary("<p>hello</p>", "other") == "hello"
    assert clean_summary("same", "same") == ""
    assert clean_summary("あ" * 90, "title").endswith("…")
    assert len(clean_summary("あ" * 90, "title")) == 81
    previous = empty_data()
    previous["note"]["items"] = [older]
    previous["youtube"]["items"] = [{"title": "video", "url": "https://www.youtube.com/watch?v=abcdefghijk", "published": "2025-03-01T00:00:00+09:00", "thumbnail": "https://i.ytimg.com/vi/abcdefghijk/mqdefault.jpg"}]
    kept = merge(previous, None, previous["youtube"]["items"])
    assert kept["note"]["items"] == [older]
    assert not items_changed(previous, kept)
    replaced = merge(previous, [newer], None)
    assert replaced["note"]["items"] == [newer]
    assert replaced["youtube"]["items"] == previous["youtube"]["items"]
    assert items_changed(previous, replaced)
    rendered = render_note([{"title": '<script>', "url": "https://note.com/okawariojisan/n/nbe72e851daed", "published": "2025-12-08T01:36:55+09:00", "summary": "ok"}])
    assert "&lt;script&gt;" in rendered
    assert "<script>" not in rendered
    page = "<!-- activity:note -->\n            <!-- /activity:note -->\n<!-- activity:youtube -->\n            <!-- /activity:youtube -->\n<time id=\"activity-updated\" datetime=\"\"></time>"
    sample = empty_data()
    sample["note"]["items"] = [newer]
    sample["youtube"]["items"] = previous["youtube"]["items"]
    output = render_page(page, sample, "2026-10-27T15:00:00+09:00")
    assert "nbbbbbbbbbbb" in output
    assert "2026-10-27 15:00 JST" in output
    print("self-test ok")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        sys.exit(update())
